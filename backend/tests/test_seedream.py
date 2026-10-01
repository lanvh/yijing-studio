import asyncio
import base64
import io
import json
import uuid
import zipfile

import httpx
import pytest
from PIL import Image
from pydantic import SecretStr

from app.core.config import get_settings
from app.providers.contracts import GenerationRequest, GenerationSettings, ImageReference
from app.providers.http_transport import ExternalServiceError
from app.providers.router import ProviderRouter
from app.providers.seedream import (
    BASE_URL,
    DEFAULT_MODEL,
    OUTPUT_SIZE,
    SeedreamHTTP,
    SeedreamImageProvider,
)
from app.schemas.generation import TaskCreate
from app.services.generation import GenerationService
from app.services.images import ImageService
from app.storage.local import LocalImageStorage
from tests import test_generation as generation_tests

BASE = generation_tests.BASE
ready = generation_tests.ready


@pytest.fixture
def configured(monkeypatch):
    for key, value in {
        "image_provider": "seedream",
        "image_api_key": SecretStr("test-seedream-key"),
        "image_api_base_url": BASE_URL,
        "image_model": DEFAULT_MODEL,
        "llm_provider": "local",
    }.items():
        monkeypatch.setattr(get_settings(), key, value)


def reply(size=OUTPUT_SIZE):
    buffer = io.BytesIO()
    Image.new("RGB", size, "#aabbcc").save(buffer, "JPEG")
    return {
        "data": [{"b64_json": base64.b64encode(buffer.getvalue()).decode()}],
        "usage": {"generated_images": 1},
    }


def service(provider):
    return ImageService(ProviderRouter(name="seedream", factories={"seedream": lambda: provider}))


@pytest.mark.parametrize("count", [1, 2, 4, 6])
def test_native_count_size_and_no_openai_fields(configured, count):
    calls = []

    def handler(request):
        calls.append(request)
        assert str(request.url) == BASE_URL + "/images/generations"
        body = json.loads(request.content)
        assert body["model"] == DEFAULT_MODEL
        assert body["size"] == "1776x2368" and body["response_format"] == "b64_json"
        assert body["watermark"] is True
        assert not any(
            field in body for field in ("n", "quality", "seed", "sequential_image_generation")
        )
        assert "避免：" in body["prompt"]
        return httpx.Response(200, json=reply(), headers={"x-request-id": "ark-request"})

    provider = SeedreamImageProvider(httpx.MockTransport(handler))
    result = asyncio.run(
        service(provider).generate(
            GenerationRequest(
                operation="create_character",
                prompt="adult model",
                settings=GenerationSettings(
                    requested_count=count, negative_prompt="distorted hands"
                ),
            )
        )
    )
    assert result.success and len(result.images) == count and len(calls) == count
    assert result.images[0].width == OUTPUT_SIZE[0] and result.cost is None
    assert result.images[0].metadata["request_id"] == "ark-request"


@pytest.mark.parametrize(
    "operation", ["virtual_try_on", "generate_content_set", "edit_image", "generate_scene"]
)
def test_reference_roles_and_inline_bytes(configured, operation):
    def handler(request):
        body = json.loads(request.content)
        assert body["image"][0] == "data:image/jpeg;base64,Y2hhcmFjdGVy"
        assert body["image"][-1] == "data:image/png;base64,cHJvZHVjdA=="
        assert len(body["image"]) == (
            10 if operation in ("virtual_try_on", "generate_content_set") else 2
        )
        return httpx.Response(200, json=reply())

    provider = SeedreamImageProvider(httpx.MockTransport(handler))
    character = ImageReference(data=b"character")
    product = ImageReference(data=b"product", media_type="image/png")
    settings = GenerationSettings(requested_count=1)
    if operation in ("virtual_try_on", "generate_content_set"):
        result = asyncio.run(
            getattr(provider, operation)((character,) * 8, (product,) * 8, "product", settings)
        )
        assert result.metadata["omitted_references"] == 6
    else:
        result = asyncio.run(
            getattr(provider, operation)((character, product), "product", settings)
        )
    assert result.success


@pytest.mark.parametrize("status", [400, 401, 403, 429, 500, 302])
def test_errors_no_retry_no_secret(configured, status):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(status, json={"error": {"message": "test-seedream-key secret"}})

    result = asyncio.run(
        SeedreamImageProvider(httpx.MockTransport(handler)).create_character(
            "adult", GenerationSettings(requested_count=1)
        )
    )
    assert not result.success and len(calls) == 1
    assert (
        "secret" not in result.model_dump_json()
        and "test-seedream-key" not in result.model_dump_json()
    )


def test_partial_and_timeout_preserve_success(configured):
    calls = []

    async def handler(request):
        calls.append(request)
        if len(calls) == 2:
            raise httpx.ReadTimeout("secret")
        return httpx.Response(200, json=reply())

    result = asyncio.run(
        SeedreamImageProvider(httpx.MockTransport(handler)).create_character(
            "adult", GenerationSettings(requested_count=2)
        )
    )
    assert not result.success and len(result.images) == 1 and result.error.code == "timeout"


@pytest.mark.parametrize(
    "value",
    [
        {"data": [{"url": "http://127.0.0.1/private"}]},
        {"data": [{"b64_json": "bad-base64"}]},
        {"data": []},
        {"data": [None]},
    ],
)
def test_bad_results_no_url_download(configured, value):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=value)

    result = asyncio.run(
        SeedreamImageProvider(httpx.MockTransport(handler)).create_character(
            "adult", GenerationSettings(requested_count=1)
        )
    )
    assert not result.success and result.error.code == "invalid_result" and len(calls) == 1


def test_config_check_no_network(configured, monkeypatch):
    for base in [
        "https://api.openai.com/v1",
        "https://ark.cn-beijing.volces.com:bad/api/v3",
        "https://untrusted.example/api/v3",
    ]:
        monkeypatch.setattr(get_settings(), "image_api_base_url", base)
        assert not asyncio.run(SeedreamImageProvider().health_check()).available
        with pytest.raises(ExternalServiceError):
            asyncio.run(SeedreamHTTP("secret", base).post("/images/generations"))
    monkeypatch.setattr(get_settings(), "image_api_base_url", BASE_URL)
    monkeypatch.setattr(get_settings(), "image_api_key", SecretStr(""))
    assert not asyncio.run(SeedreamImageProvider().health_check()).available
    assert ImageService().timeout == get_settings().image_api_timeout_seconds


def test_task_partial_retry_zip_and_reference(
    client, ready, db, user, tmp_path, configured, monkeypatch
):
    calls = []

    async def post(self, endpoint, **kwargs):
        calls.append(kwargs["json"])
        if len(calls) == 2:
            raise ExternalServiceError("模拟限流", retryable=True)
        return reply(), "ark-task"

    monkeypatch.setattr(SeedreamHTTP, "post", post)
    generator = GenerationService(db, LocalImageStorage(tmp_path))
    task = generator.create(user.id, TaskCreate(**ready))
    assert task.status == "PARTIAL" and len(task.results) == 3 and not task.is_mock
    old_ids = {r.id for r in task.results}
    task = generator.run(task.id, user.id)
    assert task.status == "SUCCEEDED" and len(task.results) == 4 and len(calls) == 5
    assert old_ids.issubset({r.id for r in task.results})
    assert task.copy.source == "local_template"
    response = client.post(BASE + "/tasks/" + str(task.id) + "/export")
    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["provider"] == "seedream" and manifest["real_generation"]
    url = "/api/v1/models/" + ready["model_id"] + "/generate-reference"
    payload = {"request_key": str(uuid.uuid4())}
    first = client.post(url, json=payload)
    assert first.status_code == 201, first.text
    assert client.post(url, json=payload).json()["id"] == first.json()["id"]
    assert len(calls) == 6
    status = client.get("/api/v1/providers")
    assert status.json()["provider"] == "seedream" and status.json()["copy_mode"] == "local"
    assert "test-seedream-key" not in status.text
