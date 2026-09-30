import io
import json
import uuid
import zipfile
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.models.generation import GenerationTask
from app.providers.mock import MockImageProvider
from app.providers.router import ProviderRouter
from app.schemas.generation import TaskCreate
from app.services.auth import AuthService
from app.services.generation import GenerationError, GenerationService
from app.services.images import ImageService
from app.storage.local import LocalImageStorage
from tests.conftest import PASSWORD
from tests.test_models import PROFILE, image_bytes

BASE = "/api/v1/generation"


@pytest.fixture
def ready(client, user, tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "local_storage_path", str(tmp_path))
    monkeypatch.setattr(get_settings(), "image_provider", "mock")
    assert (
        client.post(
            "/api/v1/auth/login", json={"email": user.email, "password": PASSWORD}
        ).status_code
        == 200
    )
    model = client.post("/api/v1/models", json=PROFILE).json()
    product = client.post(
        "/api/v1/products", json={"name": "白鞋", "category": "shoes", "color": "白色"}
    ).json()
    for kind, item in [("models", model), ("products", product)]:
        assert (
            client.post(
                f"/api/v1/{kind}/{item['id']}/images",
                files={"file": ("ref.png", image_bytes(), "image/png")},
                data={"rights_confirmed": "true"},
            ).status_code
            == 201
        )
    return dict(
        model_id=model["id"],
        product_id=product["id"],
        request_key=str(uuid.uuid4()),
        requested_count=4,
    )


def generate(client, ready):
    response = client.post(BASE + "/tasks", json=ready)
    assert response.status_code == 201, response.text
    task = response.json()
    assert task["status"] == "SUCCEEDED", task
    return task


def test_full_workflow_copy_selection_zip_and_delete(client, ready, tmp_path):
    task = generate(client, ready)
    assert len(task["results"]) == 4 and task["attempt"] == 1
    assert "snapshot" not in task and "prompt" not in task
    assert task["copy"]["source"] == "local_template"
    assert "真实试穿" in task["copy"]["caption"]
    url = BASE + "/tasks/" + task["id"]
    assert client.get(url).json()["id"] == task["id"]
    assert client.get(BASE + "/tasks?limit=1").json()["total"] == 1
    for result in task["results"]:
        assert result["identity_score"] is None and result["aesthetic_score"] is None
        assert result["metadata"]["file_check"]["scope"] == "file_integrity_only"
        assert client.get(result["image_url"]).headers["content-type"] == "image/jpeg"
    result = task["results"][-1]
    assert (
        client.patch(BASE + "/results/" + result["id"], json={"is_selected": False}).status_code
        == 200
    )
    copy = {k: v for k, v in task["copy"].items() if k != "source"}
    copy["title"] = "我的搭配草稿"
    assert client.patch(url + "/copy", json=copy).json()["source"] == "user_edited"
    zipped = client.post(url + "/export")
    assert zipped.status_code == 200
    with zipfile.ZipFile(io.BytesIO(zipped.content)) as archive:
        assert len([n for n in archive.namelist() if n.endswith(".jpg")]) == 3
        assert archive.read("title.txt").decode() == copy["title"]
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["mock"] and not manifest["real_generation"]
        assert manifest["exported_count"] == 3
        assert "character_inputs" not in archive.read("product.json").decode()
        assert archive.testzip() is None
    assert client.post(url + "/retry").status_code == 409
    assert client.delete(url).status_code == 204
    assert client.get(result["image_url"]).status_code == 404
    assert not list((tmp_path / "tasks").rglob("*.jpg"))


@pytest.mark.parametrize("count", [1, 2, 6])
def test_counts(client, ready, count):
    ready["requested_count"] = count
    assert len(generate(client, ready)["results"]) == count


def test_idempotency_validation_and_empty_export(client, ready):
    task = generate(client, ready)
    assert client.post(BASE + "/tasks", json=ready).json()["id"] == task["id"]
    assert client.get(BASE + "/tasks").json()["total"] == 1
    assert client.post(BASE + "/tasks", json={**ready, "scene": "cafe"}).status_code == 409
    assert client.post(BASE + "/tasks", json={**ready, "requested_count": 3}).status_code == 422
    assert client.post(BASE + "/tasks", json={**ready, "scene": "invalid"}).status_code == 422
    for result in task["results"]:
        client.patch(BASE + "/results/" + result["id"], json={"is_selected": False})
    assert client.post(BASE + "/tasks/" + task["id"] + "/export").status_code == 422
    assert (
        client.patch(BASE + "/tasks/" + task["id"] + "/copy", json={"title": ""}).status_code == 422
    )


def test_owner_isolation(client, ready, db):
    task = generate(client, ready)
    other = AuthService(db).create_user(
        f"other-{uuid.uuid4()}@example.com", PASSWORD, "Other", "admin"
    )
    client.post("/api/v1/auth/logout")
    client.post("/api/v1/auth/login", json={"email": other.email, "password": PASSWORD})
    url = BASE + "/tasks/" + task["id"]
    for method, path, body in [
        ("get", url, None),
        ("delete", url, None),
        ("post", url + "/retry", None),
        ("get", url + "/results", None),
        ("get", url + "/copy", None),
        ("post", url + "/copy", None),
        ("get", url + "/export", None),
        ("post", url + "/export", None),
        ("get", task["results"][0]["image_url"], None),
        ("delete", BASE + "/results/" + task["results"][0]["id"], None),
        ("patch", BASE + "/results/" + task["results"][0]["id"], {"is_selected": False}),
    ]:
        assert client.request(method, path, json=body).status_code == 404
    assert client.get(BASE + "/tasks").json()["total"] == 0
    assert (
        client.post(BASE + "/tasks", json={**ready, "request_key": str(uuid.uuid4())}).status_code
        == 404
    )


def mock_service(db, tmp_path, fail_at=()):
    return GenerationService(
        db,
        LocalImageStorage(tmp_path),
        ImageService(
            ProviderRouter(
                name="mock",
                factories={"mock": lambda: MockImageProvider(fail_at=frozenset(fail_at))},
            )
        ),
    )


def test_partial_retry_preserves_outputs_copy_and_deleted_sources(
    client, ready, db, user, tmp_path
):
    service = mock_service(db, tmp_path, (2, 3, 4))
    task = service.create(user.id, TaskCreate(**ready))
    assert task.status == "PARTIAL" and len(task.results) == 1
    original = task.results[0].id
    task.copy.title = "人工编辑保留"
    db.commit()
    for kind, key in [("models", "model_id"), ("products", "product_id")]:
        assert client.delete(f"/api/v1/{kind}/{ready[key]}").status_code == 204
    task = mock_service(db, tmp_path).run(task.id, user.id)
    assert task.status == "SUCCEEDED" and len(task.results) == 4 and task.attempt == 2
    assert original in [r.id for r in task.results]
    assert task.copy.title == "人工编辑保留"
    assert task.model_id is None and task.product_id is None
    assert client.post(BASE + "/tasks/" + str(task.id) + "/export").status_code == 200


def test_failures_limit_lease_and_result_mutations(client, ready, db, user, tmp_path):
    service = mock_service(db, tmp_path, (1, 2, 3, 4, 5, 6))
    task = service.create(user.id, TaskCreate(**ready))
    assert task.status == "FAILED"
    for _ in range(2):
        task = service.run(task.id, user.id)
    assert task.attempt == 3 and not task.can_retry
    with pytest.raises(GenerationError):
        service.run(task.id, user.id)
    task.attempt = 1
    task.status = "PROCESSING"
    task.lease_expires_at = datetime.now(UTC) + timedelta(minutes=5)
    db.commit()
    assert client.post(BASE + "/tasks/" + str(task.id) + "/retry").status_code == 409
    assert client.delete(BASE + "/tasks/" + str(task.id)).status_code == 409
    task.lease_expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db.commit()
    task = mock_service(db, tmp_path).run(task.id, user.id)
    assert task.status == "SUCCEEDED"
    result = task.results[0]
    key = result.storage_key
    assert client.delete(BASE + "/results/" + str(result.id)).status_code == 204
    assert not (tmp_path / key).exists()


def test_missing_input_and_output_storage_failure(client, ready, db, user, tmp_path, monkeypatch):
    storage = LocalImageStorage(tmp_path)
    service = GenerationService(db, storage)
    original = storage.put

    def broken(key, data):
        if "/outputs/" in key:
            raise OSError("disk unavailable")
        original(key, data)

    monkeypatch.setattr(storage, "put", broken)
    task = service.create(user.id, TaskCreate(**ready))
    assert task.status == "FAILED" and task.error_message
    assert not list(tmp_path.rglob("outputs/*.jpg"))
    task = mock_service(db, tmp_path).run(task.id, user.id)
    assert task.status == "SUCCEEDED"


def test_no_references_and_csrf(client, ready):
    empty = client.post("/api/v1/models", json=PROFILE).json()
    assert client.post(BASE + "/tasks", json={**ready, "model_id": empty["id"]}).status_code == 422
    response = client.post(BASE + "/tasks", json=ready, headers={"X-Requested-With": ""})
    assert response.status_code == 403


def test_export_detects_tampering(client, ready, db, tmp_path):
    task = generate(client, ready)
    model = db.scalar(select(GenerationTask).where(GenerationTask.id == uuid.UUID(task["id"])))
    (tmp_path / model.results[0].storage_key).write_bytes(
        image_bytes(size=(768, 1024), format="JPEG")
    )
    assert client.get(BASE + "/tasks/" + task["id"] + "/export").status_code == 409


def test_input_snapshot_failure_cleans_new_files(client, ready, db, user, tmp_path, monkeypatch):
    storage = LocalImageStorage(tmp_path)
    original = storage.put
    calls = 0

    def fail_second(key, data):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("snapshot failure")
        original(key, data)

    monkeypatch.setattr(storage, "put", fail_second)
    with pytest.raises(OSError):
        GenerationService(db, storage).create(user.id, TaskCreate(**ready))
    assert client.get(BASE + "/tasks").json()["total"] == 0
    assert not list((tmp_path / "tasks").rglob("*.jpg"))


def test_partial_storage_failure_keeps_valid_outputs(
    client, ready, db, user, tmp_path, monkeypatch
):
    storage = LocalImageStorage(tmp_path)
    original = storage.put
    calls = 0

    def fail_second_output(key, data):
        nonlocal calls
        if "/outputs/" in key:
            calls += 1
            if calls == 2:
                raise OSError("storage failure")
        original(key, data)

    monkeypatch.setattr(storage, "put", fail_second_output)
    task = GenerationService(db, storage).create(user.id, TaskCreate(**ready))
    assert task.status == "PARTIAL" and len(task.results) == 1
    first = task.results[0].id
    task = mock_service(db, tmp_path).run(task.id, user.id)
    assert task.status == "SUCCEEDED" and first in [r.id for r in task.results]


def test_finalize_commit_failure_is_recoverable(client, ready, db, user, tmp_path, monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError

    original = db.commit
    calls = 0

    def fail_final():
        nonlocal calls
        calls += 1
        if calls == 3:
            raise SQLAlchemyError("commit unavailable")
        original()

    monkeypatch.setattr(db, "commit", fail_final)
    with pytest.raises(SQLAlchemyError):
        mock_service(db, tmp_path).create(user.id, TaskCreate(**ready))
    assert not list((tmp_path / "tasks").rglob("outputs/*.jpg"))
    task = db.scalar(select(GenerationTask).where(GenerationTask.user_id == user.id))
    assert task.status == "PROCESSING"
    task.lease_expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db.commit()
    task = mock_service(db, tmp_path).run(task.id, user.id)
    assert task.status == "SUCCEEDED"


def test_stale_worker_cannot_overwrite_newer_attempt(client, ready, db, user, tmp_path):
    service = mock_service(db, tmp_path)
    wrapped = service.images

    class Superseded:
        async def generate(self, request):
            result = await wrapped.generate(request)
            task = db.scalar(select(GenerationTask).where(GenerationTask.user_id == user.id))
            task.attempt += 1
            task.status = "FAILED"
            task.error_message = "newer attempt"
            db.commit()
            return result

    service.images = Superseded()
    task = service.create(user.id, TaskCreate(**ready))
    assert task.status == "FAILED" and task.error_message == "newer attempt"
    assert not task.results
    assert not list((tmp_path / "tasks").rglob("outputs/*.jpg"))


def test_copy_regeneration_uses_snapshot(client, ready):
    task = generate(client, ready)
    url = BASE + "/tasks/" + task["id"]
    client.patch("/api/v1/products/" + ready["product_id"], json={"color": "红色"})
    copy = client.post(url + "/copy").json()
    assert copy["source"] == "local_template"
    assert "白色" in copy["product_summary"] and "红色" not in copy["product_summary"]
    assert client.get(url + "/copy").json() == copy


@pytest.mark.parametrize("data", [b"", b"not an image", image_bytes()[:45], image_bytes()])
def test_quality_rejects_invalid_or_small_files(data):
    from app.services.quality import QualityChecker

    check = QualityChecker().inspect(data)
    assert not check["passed"] and not check["visual_quality_evaluated"]


def test_prompt_contains_confirmed_facts_and_constraints(client, ready, db):
    task = generate(client, ready)
    record = db.get(GenerationTask, uuid.UUID(task["id"]))
    assert "白色" in record.prompt
    for phrase in [
        "character identity",
        "product color",
        "structure",
        "logos",
        "hands and feet",
        "lighting",
    ]:
        assert phrase in record.prompt
    assert "extra fingers" in record.negative_prompt
    assert len(record.prompt) <= 6000
