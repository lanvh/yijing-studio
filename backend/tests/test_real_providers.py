import asyncio
import base64
import io
import json
import uuid

import httpx
import pytest
from PIL import Image
from pydantic import SecretStr

from app.core.config import get_settings
from app.providers.contracts import GenerationSettings, ImageReference
from app.providers.openai_http import ExternalServiceError, OpenAIHTTP
from app.providers.openai_images import OpenAIImageProvider
from app.providers.openai_text import OpenAITextProvider
from app.providers.router import ProviderRouter
from app.services.images import ImageService
from tests import test_generation as generation_tests

BASE = generation_tests.BASE
generate = generation_tests.generate
ready = generation_tests.ready


def picture():
    buffer = io.BytesIO()
    Image.new("RGB", (768, 1024), "#aabbcc").save(buffer, "JPEG")
    return buffer.getvalue()


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setattr(get_settings(), "image_api_key", SecretStr("unit-test-not-a-real-key"))
    monkeypatch.setattr(get_settings(), "image_model", "gpt-image-2.5-sunburst")
    monkeypatch.setattr(get_settings(), "image_api_base_url", "")
    monkeypatch.setattr(get_settings(), "llm_api_key", SecretStr("unit-test-not-a-real-key"))


def image_reply(count=1):
    return {
        "data": [{"b64_json": base64.b64encode(picture()).decode()} for _ in range(count)],
        "usage": {"total_tokens": 123},
    }


def test_image_generation_contract_and_usage(configured):
    calls = []

    def handler(request):
        calls.append(request)
        body = json.loads(request.content)
        assert body["n"] == 2 and body["size"] == "768x1024"
        assert body["output_format"] == "jpeg" and "seed" not in body
        return httpx.Response(200, json=image_reply(2), headers={"x-request-id": "request-123"})

    provider = OpenAIImageProvider(httpx.MockTransport(handler))
    result = asyncio.run(
        provider.create_character("adult fictional model", GenerationSettings(requested_count=2))
    )
    assert result.success and len(result.images) == 2 and result.cost is None
    assert result.metadata["usage"]["total_tokens"] == 123
    assert result.provider_task_id == "request-123"
    assert not result.metadata["mock"]
    assert calls[0].url.path == "/v1/images/generations"


@pytest.mark.parametrize(
    "operation", ["virtual_try_on", "generate_content_set", "edit_image", "generate_scene"]
)
def test_edit_multipart_reference_order(configured, operation):
    def handler(request):
        assert request.url.path == "/v1/images/edits"
        assert b'name="image[]"' in request.content
        assert b"negative" in request.content
        return httpx.Response(200, json=image_reply())

    provider = OpenAIImageProvider(httpx.MockTransport(handler))
    refs = (ImageReference(data=picture()),)
    settings = GenerationSettings(requested_count=1, negative_prompt="negative")
    if operation in ("virtual_try_on", "generate_content_set"):
        call = getattr(provider, operation)(refs, refs, "preserve", settings)
    else:
        call = getattr(provider, operation)(refs, "preserve", settings)
    assert asyncio.run(call).success


@pytest.mark.parametrize(
    "status,code",
    [
        (400, "invalid_input"),
        (401, "unavailable"),
        (403, "unavailable"),
        (429, "unavailable"),
        (500, "unavailable"),
        (302, "unavailable"),
    ],
)
def test_upstream_errors_are_safe_and_not_retried(configured, status, code):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(
            status, json={"error": {"message": "secret unit-test-not-a-real-key"}}
        )

    result = asyncio.run(
        OpenAIImageProvider(httpx.MockTransport(handler)).create_character(
            "model", GenerationSettings(requested_count=1)
        )
    )
    assert not result.success and result.error.code == code and len(calls) == 1
    assert "secret" not in result.model_dump_json()


def test_partial_invalid_images_preserve_valid(configured):
    def handler(request):
        value = image_reply()
        value["data"].append({"b64_json": "invalid"})
        return httpx.Response(200, json=value)

    result = asyncio.run(
        OpenAIImageProvider(httpx.MockTransport(handler)).create_character(
            "model", GenerationSettings(requested_count=2)
        )
    )
    assert not result.success and len(result.images) == 1


def test_refuses_result_url_download_and_oversized_body(configured):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"data": [{"url": "http://127.0.0.1/private"}]})

    result = asyncio.run(
        OpenAIImageProvider(httpx.MockTransport(handler)).create_character(
            "model", GenerationSettings(requested_count=1)
        )
    )
    assert not result.success and len(calls) == 1
    with pytest.raises(ExternalServiceError):
        asyncio.run(
            OpenAIHTTP(
                "test",
                transport=httpx.MockTransport(
                    lambda request: httpx.Response(200, content=b"x" * 101)
                ),
            ).post("/responses", max_bytes=100)
        )


def test_key_and_host_validation_without_network(monkeypatch):
    monkeypatch.setattr(get_settings(), "image_api_key", SecretStr(""))
    assert not asyncio.run(OpenAIImageProvider().health_check()).available
    monkeypatch.setattr(get_settings(), "image_api_key", SecretStr("test"))
    for base in (
        "https://untrusted.example/v1",
        "https://api.openai.com:invalid/v1",
        "https://[broken/v1",
    ):
        monkeypatch.setattr(get_settings(), "image_api_base_url", base)
        assert not asyncio.run(OpenAIImageProvider().health_check()).available
        with pytest.raises(ExternalServiceError):
            asyncio.run(OpenAIHTTP("test", base).post("/responses"))


def test_timeout_not_retried(configured):
    def handler(request):
        raise httpx.ReadTimeout("private request detail")

    result = asyncio.run(
        OpenAIImageProvider(httpx.MockTransport(handler)).create_character(
            "model", GenerationSettings(requested_count=1)
        )
    )
    assert result.error.code == "timeout" and "private" not in result.error.message


def text_reply(data):
    return {
        "status": "completed",
        "output": [
            {
                "type": "message",
                "content": [{"type": "output_text", "text": json.dumps(data, ensure_ascii=False)}],
            }
        ],
    }


COPY = {
    "title": "白鞋搭配",
    "caption": "白色运动鞋的搭配灵感。",
    "hashtags": ["搭配"],
    "product_summary": "颜色：白色",
    "styling_notes": "自然光搭配。",
}
FINDINGS = {
    "category": "shoes",
    "colors": ["白色"],
    "pattern": "",
    "logo_description": "",
    "shape": "低帮",
    "material_appearance": "表面有织物纹理",
    "critical_features": ["系带"],
    "uncertainties": ["无法从图片判断实际材质"],
}


def test_structured_copy_and_vision_contract(configured):
    def handler(request):
        body = json.loads(request.content)
        assert body["store"] is False and body["text"]["format"]["strict"]
        assert body["max_output_tokens"] == 3000
        vision = len(body["input"][0]["content"]) > 1
        if vision:
            assert body["input"][0]["content"][1]["image_url"].startswith("data:image/jpeg;base64,")
        return httpx.Response(200, json=text_reply(FINDINGS if vision else COPY))

    provider = OpenAITextProvider(httpx.MockTransport(handler))
    assert asyncio.run(provider.copy({"color": "white"})).title == COPY["title"]
    assert asyncio.run(provider.analyze({}, [picture()])).shape == "低帮"


@pytest.mark.parametrize(
    "reply",
    [
        {"status": "incomplete", "output": []},
        {"status": "completed", "output": []},
        {"status": "completed", "output": None},
        text_reply({"title": "missing fields"}),
    ],
)
def test_invalid_text_responses_are_safe(configured, reply):
    provider = OpenAITextProvider(
        httpx.MockTransport(lambda request: httpx.Response(200, json=reply))
    )
    with pytest.raises(ExternalServiceError):
        asyncio.run(provider.copy({}))


def test_real_task_and_zip_provenance(client, ready, db, user, tmp_path, configured, monkeypatch):
    from app.schemas.generation import TaskCreate
    from app.services.generation import GenerationService
    from app.storage.local import LocalImageStorage

    monkeypatch.setattr(get_settings(), "image_provider", "openai")

    def handler(request):
        # This test isolates the external API; all task/DB/storage/export work is real.
        return httpx.Response(200, json=image_reply(4))

    provider = OpenAIImageProvider(httpx.MockTransport(handler))
    images = ImageService(ProviderRouter(name="openai", factories={"openai": lambda: provider}))
    task = GenerationService(db, LocalImageStorage(tmp_path), images).create(
        user.id, TaskCreate(**ready)
    )
    assert task.status == "SUCCEEDED" and not task.is_mock
    import zipfile

    response = client.post(BASE + "/tasks/" + str(task.id) + "/export")
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["real_generation"] and not manifest["mock"]
        assert "Mock" not in archive.read("README.txt").decode()


def test_ai_copy_failure_preserves_images(client, ready, monkeypatch):
    async def fail(*args):
        raise ExternalServiceError("unavailable")

    monkeypatch.setattr(get_settings(), "llm_provider", "openai")
    monkeypatch.setattr(OpenAITextProvider, "copy", fail)
    task = generate(client, ready)
    assert task["copy"]["source"] == "local_fallback"
    assert client.post(BASE + "/tasks/" + task["id"] + "/copy").status_code == 503


def test_generated_character_reference_idempotency_and_ownership(client, ready, db, user):
    url = "/api/v1/models/" + ready["model_id"] + "/generate-reference"
    key = str(uuid.uuid4())
    response = client.post(url, json={"request_key": key})
    assert response.status_code == 201, response.text
    image = response.json()
    assert image["metadata"]["mock"]
    assert client.post(url, json={"request_key": key}).json()["id"] == image["id"]
    assert client.get(image["image_url"]).status_code == 200
    assert (
        client.post(
            "/api/v1/models/" + str(uuid.uuid4()) + "/generate-reference", json={}
        ).status_code
        == 404
    )


def test_ai_product_suggestions_do_not_override_confirmed(client, ready, monkeypatch):
    from app.providers.openai_text import VisualFindings

    async def analyze(*args):
        return VisualFindings(**FINDINGS)

    monkeypatch.setattr(OpenAITextProvider, "analyze", analyze)
    monkeypatch.setattr(get_settings(), "llm_provider", "openai")
    url = "/api/v1/products/" + ready["product_id"]
    client.patch(url, json={"feature_notes": {"material": "人工确认的皮革"}})
    response = client.post(url + "/analyze")
    assert response.status_code == 200, response.text
    features = response.json()["product_features"]
    assert features["confirmed"]["material"] == "人工确认的皮革"
    assert features["ai_analysis"]["confirmed"] is False
    assert (
        features["ai_analysis"]["findings"]["material_appearance"]
        == FINDINGS["material_appearance"]
    )


def test_dashboard_stats_and_secret_free_status(client, ready, configured):
    generate(client, ready)
    stats = client.get(BASE + "/stats").json()
    assert stats["models"] == 1 and stats["products"] == 1
    assert stats["tasks"] == 1 and stats["succeeded_tasks"] == 1
    response = client.get("/api/v1/providers")
    assert "unit-test" not in response.text


def test_ai_copy_success_and_unsubstantiated_claim_fallback(client, ready, monkeypatch):
    from app.schemas.generation import CopyEdit

    async def valid_copy(*args):
        return CopyEdit(**COPY)

    monkeypatch.setattr(get_settings(), "llm_provider", "openai")
    monkeypatch.setattr(OpenAITextProvider, "copy", valid_copy)
    task = generate(client, ready)
    assert task["copy"]["source"] == "openai"
    assert "Mock" in task["copy"]["caption"]

    async def unsafe_copy(*args):
        return CopyEdit(**{**COPY, "caption": "我穿了一周，实测绝对舒服"})

    monkeypatch.setattr(OpenAITextProvider, "copy", unsafe_copy)
    response = client.post(BASE + "/tasks/" + task["id"] + "/copy")
    assert response.status_code == 503
    assert client.get(BASE + "/tasks/" + task["id"] + "/copy").json()["title"] == COPY["title"]
