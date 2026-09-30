import asyncio
import hashlib
import io
import json
import socket

import pytest
from PIL import Image
from pydantic import ValidationError

from app.core.config import get_settings
from app.mock_job import main, make_demo_request
from app.providers.contracts import (
    OPERATIONS,
    GenerationRequest,
    GenerationSettings,
    ImageReference,
    ProviderError,
    ProviderResult,
)
from app.providers.mock import MockImageProvider
from app.providers.router import ProviderRouter, ProviderUnavailable
from app.services.images import ImageService
from app.services.mock_jobs import MockJobRunner
from app.storage.local import LocalImageStorage
from tests.conftest import PASSWORD


def run(awaitable):
    return asyncio.run(awaitable)


def request(operation="create_character", count=2):
    demo = make_demo_request(operation, count, 42)
    return demo.model_copy(
        update={
            "settings": GenerationSettings(requested_count=count, width=256, height=320, seed=42)
        }
    )


def service(provider=None, **kwargs):
    return ImageService(
        ProviderRouter(name="mock", factories={"mock": lambda: provider or MockImageProvider()}),
        **kwargs,
    )


@pytest.mark.parametrize("operation", OPERATIONS)
@pytest.mark.parametrize("count", [1, 2, 4, 6])
def test_operations_and_counts_without_network(operation, count, monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("Mock must not contact the network")

    monkeypatch.delenv("IMAGE_API_KEY", raising=False)

    async def invoke_offline():
        # Windows asyncio creates a loopback socketpair before running the coroutine.
        # Block all connects only during the provider call, after event-loop setup.
        with monkeypatch.context() as isolated:
            isolated.setattr(socket.socket, "connect", no_network)
            return await service().generate(request(operation, count))

    result = run(invoke_offline())
    assert result.success and result.error is None and result.cost == 0
    assert result.provider == "mock"
    assert len(result.images) == count
    assert len({image.id for image in result.images}) == count
    assert result.metadata["outcome"] == "SUCCEEDED"
    assert result.metadata["mock"] is True
    assert result.metadata["references_used"] is False
    assert len({image.data for image in result.images}) == count
    for image in result.images:
        assert image.metadata["aigc_label"] == "mock_placeholder"
        assert image.metadata["sha256"] == hashlib.sha256(image.data).hexdigest()
        with Image.open(io.BytesIO(image.data)) as decoded:
            decoded.load()
            assert decoded.format == "JPEG" and decoded.size == (256, 320)
    # Serializable metadata never includes raw image bytes.
    serialized = result.model_dump(mode="json")
    assert all("data" not in image for image in serialized["images"])


def test_deterministic_images_and_unique_job_identity():
    first = run(service().generate(request()))
    second = run(service().generate(request()))
    assert first.provider_task_id != second.provider_task_id
    assert [image.data for image in first.images] == [image.data for image in second.images]
    changed = request().model_copy(
        update={"settings": request().settings.model_copy(update={"seed": 43})}
    )
    assert run(service().generate(changed)).images[0].data != first.images[0].data


@pytest.mark.parametrize(
    "values",
    [
        {"requested_count": 0},
        {"requested_count": 3},
        {"requested_count": 7},
        {"requested_count": True},
        {"requested_count": "4"},
        {"width": 255},
        {"height": 1537},
        {"seed": -1},
        {"seed": 4294967296},
        {"negative_prompt": "x" * 3001},
        {"vendor_key": "should-not-be-here"},
    ],
)
def test_invalid_settings(values):
    with pytest.raises(ValidationError):
        GenerationSettings(**values)


@pytest.mark.parametrize(
    "values",
    [
        {"prompt": ""},
        {"prompt": "   "},
        {"prompt": "x" * 6001},
        {"operation": "unsupported"},
        {"image_url": "https://untrusted.example/image.jpg"},
        {"reference_images": [{"path": "../../secret"}]},
    ],
)
def test_invalid_requests(values):
    with pytest.raises(ValidationError):
        GenerationRequest(**{"operation": "create_character", "prompt": "test", **values})


@pytest.mark.parametrize(
    "operation", ["virtual_try_on", "generate_content_set", "edit_image", "generate_scene"]
)
def test_required_reference_groups(operation):
    with pytest.raises(ValidationError):
        GenerationRequest(operation=operation, prompt="test")


def test_mock_rejects_missing_references_and_blank_prompt():
    provider = MockImageProvider()
    result = run(provider.virtual_try_on((), (), "test", GenerationSettings()))
    assert not result.success and result.error.code == "invalid_input"
    result = run(provider.create_character(" ", GenerationSettings()))
    assert not result.success and result.error.code == "invalid_input"
    with pytest.raises(ValidationError):
        ImageReference(data=b"")
    demo = make_demo_request("edit_image", 1, 0)
    with pytest.raises(ValidationError):
        GenerationRequest(
            operation="edit_image", prompt="test", reference_images=demo.reference_images * 9
        )


@pytest.mark.parametrize(
    "failed,outcome,expected",
    [
        (frozenset({2}), "PARTIAL", 3),
        (frozenset({1, 2, 3, 4}), "FAILED", 0),
    ],
)
def test_partial_and_complete_failure(failed, outcome, expected):
    result = run(service(MockImageProvider(fail_at=failed)).generate(request(count=4)))
    assert not result.success
    assert result.metadata["outcome"] == outcome
    assert len(result.images) == expected
    assert result.error.code == "generation_failed"
    assert result.error.retryable
    assert result.metadata["failed_indices"] == sorted(failed)


def test_provider_router_does_not_fall_back():
    with pytest.raises(ProviderUnavailable):
        ProviderRouter(name="unimplemented").select()
    result = run(ImageService(ProviderRouter(name="unimplemented")).generate(request()))
    assert not result.success and result.error.code == "unavailable"
    health = run(ImageService(ProviderRouter(name="unimplemented")).health_check())
    assert not health.available and health.requires_api_key is None


def test_provider_timeout_and_cancellation():
    class SlowProvider(MockImageProvider):
        cancelled = False

        async def create_character(self, prompt, settings):
            try:
                await asyncio.sleep(10)
            finally:
                self.cancelled = True

        async def health_check(self):
            await asyncio.sleep(10)

    slow = SlowProvider()
    result = run(service(slow, timeout_seconds=0.01).generate(request()))
    assert result.error.code == "timeout" and result.error.retryable
    assert slow.cancelled
    assert not run(service(slow, timeout_seconds=0.01).health_check()).available


def test_errors_do_not_expose_credentials_or_prompt(caplog):
    secret = "vendor-key-secret-do-not-expose"

    class BrokenProvider(MockImageProvider):
        async def create_character(self, prompt, settings):
            raise RuntimeError(secret)

        async def health_check(self):
            raise RuntimeError(secret)

    result = run(service(BrokenProvider()).generate(request()))
    assert result.error.code == "internal_error"
    health = run(service(BrokenProvider()).health_check())
    assert not health.available
    assert secret not in result.model_dump_json() + health.model_dump_json() + caplog.text


@pytest.mark.parametrize("kind", ["count", "bytes", "truncated", "size", "duplicate", "provider"])
def test_invalid_provider_result_is_rejected(kind):
    class InvalidProvider(MockImageProvider):
        async def create_character(self, prompt, settings):
            result = await super().create_character(prompt, settings)
            if kind == "count":
                result.images.pop()
            elif kind == "bytes":
                result.images[0].data = b"not an image"
            elif kind == "truncated":
                result.images[0].data = result.images[0].data[:-200]
            elif kind == "size":
                result.images[0].width += 1
            elif kind == "duplicate":
                result.images[1].id = result.images[0].id
            elif kind == "provider":
                result.provider = "unexpected"
            return result

    result = run(service(InvalidProvider()).generate(request()))
    assert result.error.code == "invalid_result"
    assert result.images == []


def test_result_invariants():
    with pytest.raises(ValidationError):
        ProviderResult(success=True, provider="mock")
    with pytest.raises(ValidationError):
        ProviderResult(success=False, provider="mock")


def test_local_job_saves_images_and_manifest(tmp_path):
    storage = LocalImageStorage(tmp_path)
    key, manifest = run(MockJobRunner(service(), storage).run(request("generate_content_set", 4)))
    assert key.startswith("mock_jobs/")
    assert manifest["development_only"] is True
    assert manifest["result"]["success"]
    assert json.loads(storage.read(key)) == manifest
    for image in manifest["result"]["images"]:
        assert storage.read(image["storage_key"]).startswith(b"\xff\xd8")
        assert "data" not in image
    assert len([p for p in tmp_path.rglob("*") if p.is_file()]) == 5


def test_local_job_write_failure_cleans_files(tmp_path):
    class BrokenStorage(LocalImageStorage):
        calls = 0

        def put(self, key, data):
            self.calls += 1
            if self.calls == 2:
                raise OSError("simulated write failure")
            super().put(key, data)

    with pytest.raises(OSError):
        run(MockJobRunner(service(), BrokenStorage(tmp_path)).run(request()))
    assert not [p for p in tmp_path.rglob("*") if p.is_file()]


def test_local_cli_success_partial_failure_and_validation(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(get_settings(), "local_storage_path", str(tmp_path))
    monkeypatch.setattr(get_settings(), "image_provider", "mock")
    assert main(["--count", "1"]) == 0
    assert main(["--count", "2", "--simulate-failure-at", "2"]) == 2
    assert main(["--count", "1", "--simulate-failure-at", "1"]) == 2
    output = capsys.readouterr().out
    assert "SUCCEEDED" in output and "PARTIAL" in output and "FAILED" in output
    with pytest.raises(SystemExit) as error:
        main(["--count", "1", "--simulate-failure-at", "2"])
    assert error.value.code == 2
    monkeypatch.setattr(get_settings(), "image_provider", "unimplemented")
    with pytest.raises(SystemExit):
        main([])


def test_provider_status_authentication_and_configuration(client, user, monkeypatch):
    assert client.get("/api/v1/providers").status_code == 401
    client.post("/api/v1/auth/login", json={"email": user.email, "password": PASSWORD})
    monkeypatch.setattr(get_settings(), "image_provider", "mock")
    response = client.get("/api/v1/providers")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["operations"] == list(OPERATIONS)
    assert response.json()["requires_api_key"] is False
    monkeypatch.setattr(get_settings(), "image_provider", "unimplemented")
    response = client.get("/api/v1/providers")
    assert response.json()["available"] is False
    assert response.json()["operations"] == []
    # Business task endpoints remain reserved for Phase 5.
    assert client.post("/api/v1/generation/tasks", json={}).status_code == 404


def test_provider_job_id_allows_vendor_native_identifiers():
    result = ProviderResult(
        success=False,
        provider="adapter-test",
        provider_task_id="vendor-job-42",
        error=ProviderError(code="generation_failed", message="test failure"),
    )
    assert result.provider_task_id == "vendor-job-42"
