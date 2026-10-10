import base64
import io
import uuid
from urllib.parse import urlsplit

from PIL import Image

from app.core.config import get_settings
from app.models.generation import GenerationTask
from tests import test_generation as workflow

ready = workflow.ready


def link(client, ready, monkeypatch):
    monkeypatch.setattr(get_settings(), "mobile_public_url", "http://192.168.31.68:5173")
    task = workflow.generate(client, ready)
    endpoint = workflow.BASE + "/tasks/" + task["id"] + "/mobile-transfer"
    response = client.post(endpoint)
    assert response.status_code == 200
    value = response.json()
    return task, endpoint, value, {"X-Mobile-Token": urlsplit(value["url"]).fragment}


def test_phone_scoped_content_qr_without_login(client, ready, monkeypatch):
    task, _, value, headers = link(client, ready, monkeypatch)
    assert value["url"].startswith("http://192.168.31.68:5173/mobile-publish/")
    assert Image.open(io.BytesIO(base64.b64decode(value["qr_image"].split(",")[1]))).format == "PNG"
    base = "/api/v1/mobile-publish/" + task["id"]
    client.post("/api/v1/auth/logout")
    response = client.get(base, headers=headers)
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    assert set(response.json()) == {"title", "caption", "hashtags", "expires_at", "images"}
    assert len(response.json()["images"]) == 4
    image = client.get(base + "/images/" + task["results"][0]["id"], headers=headers)
    assert image.status_code == 200 and image.headers["content-type"] == "image/jpeg"
    assert client.get(base).status_code == 404
    assert client.get(base, headers={"X-Mobile-Token": "wrong"}).status_code == 404
    assert client.get(workflow.BASE + "/tasks/" + task["id"]).status_code == 401


def test_rotating_revoking_and_expiring_link(client, ready, monkeypatch, db):
    task, endpoint, _, old = link(client, ready, monkeypatch)
    base = "/api/v1/mobile-publish/" + task["id"]
    value = client.post(endpoint).json()
    headers = {"X-Mobile-Token": urlsplit(value["url"]).fragment}
    assert client.get(base, headers=old).status_code == 404
    record = db.get(GenerationTask, uuid.UUID(task["id"]))
    assert urlsplit(value["url"]).fragment not in str(record.snapshot)
    record.snapshot = {
        **record.snapshot,
        "mobile_transfer": {**record.snapshot["mobile_transfer"], "expires_at": 1},
    }
    db.commit()
    assert client.get(base, headers=headers).status_code == 404
    value = client.post(endpoint).json()
    headers = {"X-Mobile-Token": urlsplit(value["url"]).fragment}
    assert client.delete(endpoint).status_code == 204
    assert client.get(base, headers=headers).status_code == 404


def test_unselected_deleted_and_other_task_images_denied(client, ready, monkeypatch):
    task, _, _, headers = link(client, ready, monkeypatch)
    base = "/api/v1/mobile-publish/" + task["id"]
    result = task["results"][0]
    client.patch(workflow.BASE + "/results/" + result["id"], json={"is_selected": False})
    assert len(client.get(base, headers=headers).json()["images"]) == 3
    assert client.get(base + "/images/" + result["id"], headers=headers).status_code == 404
    assert client.get(base + "/images/" + str(uuid.uuid4()), headers=headers).status_code == 404
    client.delete(workflow.BASE + "/tasks/" + task["id"])
    assert client.get(base, headers=headers).status_code == 404


def test_share_requires_selected_copy_and_owner(client, ready, monkeypatch):
    task, endpoint, _, _ = link(client, ready, monkeypatch)
    for image in task["results"]:
        client.patch(workflow.BASE + "/results/" + image["id"], json={"is_selected": False})
    assert client.post(endpoint).status_code == 422
    assert (
        client.post(workflow.BASE + "/tasks/" + str(uuid.uuid4()) + "/mobile-transfer").status_code
        == 404
    )
    client.post("/api/v1/auth/logout")
    assert client.post(endpoint).status_code == 401
    assert client.delete(endpoint).status_code == 401


def test_other_account_cannot_create_or_revoke(client, ready, monkeypatch, db):
    from app.services.auth import AuthService
    from tests.conftest import PASSWORD

    task, endpoint, _, _ = link(client, ready, monkeypatch)
    other = AuthService(db).create_user(
        f"phone-{uuid.uuid4().hex}@example.com", PASSWORD, "另一个用户", "user"
    )
    client.post("/api/v1/auth/login", json={"email": other.email, "password": PASSWORD})
    assert client.post(endpoint).status_code == 404
    assert client.delete(endpoint).status_code == 404
