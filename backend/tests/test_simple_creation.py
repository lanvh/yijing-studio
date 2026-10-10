import asyncio
import io
import json
from pathlib import Path

import httpx
import pytest
from PIL import Image
from pydantic import SecretStr

from app.core.config import get_settings
from app.providers.ark_text import ArkTextProvider
from app.providers.http_transport import ExternalServiceError
from app.providers.seedream import BASE_URL
from tests import test_generation as generation_tests
from tests.test_real_providers import COPY, FINDINGS

ready = generation_tests.ready
generate = generation_tests.generate
BASE = generation_tests.BASE


def completion(data):
    return {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(data)}}]}


@pytest.fixture
def ark(monkeypatch):
    for key, value in {
        "llm_provider": "ark",
        "llm_model": "doubao-seed-2-1-lite-260915",
        "llm_api_base_url": BASE_URL,
        "llm_api_key": SecretStr("fake-key"),
    }.items():
        monkeypatch.setattr(get_settings(), key, value)


def test_minimal_profiles_and_preserve_legacy_fields(client, ready):
    model = client.post("/api/v1/models", json={"name": "简洁模特", "gender": "male"})
    assert model.status_code == 201
    url = "/api/v1/models/" + model.json()["id"]
    client.patch(url, json={"hair_color": "黑色"})
    assert client.patch(url, json={"name": "改名", "gender": "male"}).json()["hair_color"] == "黑色"
    product = client.post("/api/v1/products", json={"name": "开衫"})
    assert product.status_code == 201 and product.json()["category"] == "other"


def test_custom_direction_snapshot_prompt_idempotency_and_export(client, ready, db):
    from app.services.generation import GenerationService
    from app.storage.local import LocalImageStorage

    ready.update(
        scene="bookstore",
        style="preppy",
        pose="holding_coffee",
        custom_direction="雨后的复古书店，暖色胶片光线",
    )
    task = generate(client, ready)
    assert task["custom_direction"] == ready["custom_direction"]
    saved = GenerationService(db, LocalImageStorage(Path(get_settings().local_storage_path))).owned(
        task["id"], task_user(db, task["id"])
    )
    assert ready["custom_direction"] in saved.prompt
    assert "Reference photos are authoritative" in saved.prompt
    assert "25-34" not in saved.prompt
    duplicate = client.post(BASE + "/tasks", json=ready)
    assert duplicate.json()["id"] == task["id"]
    assert (
        client.post(BASE + "/tasks", json={**ready, "custom_direction": "另外一个场景"}).status_code
        == 409
    )
    assert (
        client.get(BASE + "/tasks/" + task["id"]).json()["custom_direction"]
        == ready["custom_direction"]
    )
    assert (
        client.post(BASE + "/tasks", json={**ready, "custom_direction": "x" * 1201}).status_code
        == 422
    )
    assert client.post(BASE + "/tasks", json={**ready, "scene": "invalid"}).status_code == 422


def task_user(db, task_id):
    import uuid

    from app.models.generation import GenerationTask

    return db.get(GenerationTask, uuid.UUID(task_id)).user_id


def test_ark_copy_and_vision_request_are_official_and_structured(ark):
    calls = []

    def handler(request):
        calls.append(request)
        assert str(request.url) == BASE_URL + "/chat/completions"
        body = json.loads(request.content)
        assert (
            body["thinking"] == {"type": "disabled"}
            and body["response_format"]["type"] == "json_object"
        )
        assert "JSON" in body["messages"][0]["content"]
        if len(calls) == 1:
            assert body["messages"][1]["content"][1]["type"] == "image_url"
            assert "2到3个短段落" in body["messages"][0]["content"]
            return httpx.Response(200, json=completion(COPY))
        return httpx.Response(200, json=completion(FINDINGS))

    provider = ArkTextProvider(httpx.MockTransport(handler))
    assert asyncio.run(provider.copy({}, [b"jpeg"])).title == COPY["title"]
    assert asyncio.run(provider.analyze({}, [b"jpeg"])).shape == FINDINGS["shape"]


@pytest.mark.parametrize(
    "value",
    [
        {},
        {"choices": []},
        {"choices": [{"finish_reason": "length"}]},
        completion({"title": "不完整"}),
    ],
)
def test_ark_malformed_or_truncated_output_is_safe(ark, value):
    provider = ArkTextProvider(httpx.MockTransport(lambda r: httpx.Response(200, json=value)))
    with pytest.raises(ExternalServiceError):
        asyncio.run(provider.copy({}))


def test_copy_images_observations_and_fallback(client, ready, ark, monkeypatch):
    seen = []

    async def copy(self, facts, images):
        from app.schemas.generation import CopyEdit

        seen.append((facts, images))
        return CopyEdit(**COPY)

    monkeypatch.setattr(ArkTextProvider, "copy", copy)
    task = generate(client, ready)
    assert task["copy"]["source"] == "ark" and seen[0][1]
    assert "visible_observations_not_verified_facts" in seen[0][0]

    async def failed(*args):
        raise ExternalServiceError("无模型权限")

    monkeypatch.setattr(ArkTextProvider, "copy", failed)
    before = task["copy"]
    assert client.post(BASE + "/tasks/" + task["id"] + "/copy").status_code == 503
    assert client.get(BASE + "/tasks/" + task["id"]).json()["copy"] == before


def test_photo_analysis_keeps_unknown_material_and_preserves_user_fields(
    client, ready, ark, monkeypatch
):
    async def analyze(*args):
        from app.providers.openai_text import VisualFindings

        return VisualFindings(**{**FINDINGS, "category": "top"})

    monkeypatch.setattr(ArkTextProvider, "analyze", analyze)
    product = client.post("/api/v1/products", json={"name": "开衫"}).json()
    data = io.BytesIO()
    Image.new("RGB", (96, 128), "red").save(data, "PNG")
    result = client.post(
        "/api/v1/products/" + product["id"] + "/images",
        files={"file": ("ref.png", data.getvalue(), "image/png")},
        data={"rights_confirmed": "true"},
    )
    assert result.status_code == 201
    value = result.json()
    assert value["category"] == "top"
    assert value["product_features"]["ai_analysis"]["source"] == "ark"
    assert not value["product_features"]["confirmed"]["material"]
