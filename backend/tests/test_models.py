import io
import uuid

import pytest
from PIL import Image
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.models.ai_model import AIModel, AIModelImage
from app.services.auth import AuthService
from tests.conftest import PASSWORD

PROFILE = {
    "name": "Female Casual",
    "gender": "female",
    "age_range": "25-34",
    "height": 168,
    "body_type": "匀称",
    "skin_tone": "自然",
    "hair_style": "中长发",
    "hair_color": "黑色",
    "style": "casual",
    "description": "成年虚拟人物，自然休闲风格。",
}


def image_bytes(format="PNG", size=(96, 128)):
    out = io.BytesIO()
    Image.new("RGB", size, "#93a887").save(out, format=format)
    return out.getvalue()


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "local_storage_path", str(tmp_path))
    return tmp_path


@pytest.fixture
def signed_in(client, user):
    assert (
        client.post(
            "/api/v1/auth/login",
            json={
                "email": user.email,
                "password": PASSWORD,
            },
        ).status_code
        == 200
    )
    return client


@pytest.fixture
def model(signed_in):
    response = signed_in.post("/api/v1/models", json=PROFILE)
    assert response.status_code == 201
    return response.json()


def upload(client, model_id, *, data=None, name="reference.png", mime="image/png", consent="true"):
    return client.post(
        f"/api/v1/models/{model_id}/images",
        files={"file": (name, data if data is not None else image_bytes(), mime)},
        data={"rights_confirmed": consent},
    )


def test_create_list_detail_edit_delete(signed_in, model):
    assert model["name"] == "Female Casual"
    assert model["reference_images"] == []
    assert "provider_metadata" not in model
    listing = signed_in.get("/api/v1/models").json()
    assert model["id"] in [item["id"] for item in listing["items"]]
    detail = signed_in.get(f"/api/v1/models/{model['id']}")
    assert detail.json()["height"] == 168
    changed = signed_in.patch(
        f"/api/v1/models/{model['id']}",
        json={
            "name": "Male Streetwear",
            "gender": "male",
            "height": None,
            "description": "",
        },
    )
    assert changed.status_code == 200
    assert changed.json()["name"] == "Male Streetwear"
    assert changed.json()["height"] is None
    assert changed.json()["style"] == "casual"
    assert signed_in.delete(f"/api/v1/models/{model['id']}").status_code == 204
    assert signed_in.get(f"/api/v1/models/{model['id']}").status_code == 404


def test_search_pagination_and_literal_wildcard(signed_in):
    prefix = uuid.uuid4().hex
    for name in [prefix + "-100%", prefix + "-other", prefix + "-third"]:
        assert signed_in.post("/api/v1/models", json={**PROFILE, "name": name}).status_code == 201
    page = signed_in.get("/api/v1/models", params={"q": prefix, "limit": 1, "offset": 1}).json()
    assert page["total"] == 3
    assert len(page["items"]) == 1
    matches = signed_in.get("/api/v1/models", params={"q": prefix + "-100%"}).json()
    assert matches["total"] == 1
    assert signed_in.get("/api/v1/models", params={"limit": 101}).status_code == 422


@pytest.mark.parametrize(
    "changes",
    [
        {"name": "  "},
        {"name": "a" * 101},
        {"age_range": "under18"},
        {"height": 99},
        {"height": 251},
        {"height": "168"},
        {"gender": "invalid"},
        {"description": "x" * 2001},
        {"user_id": str(uuid.uuid4())},
        {"provider_metadata": {"bypass": True}},
    ],
)
def test_invalid_create(signed_in, changes):
    assert signed_in.post("/api/v1/models", json={**PROFILE, **changes}).status_code == 422


@pytest.mark.parametrize("changes", [{"name": None}, {"style": None}, {"id": "new"}])
def test_invalid_patch(signed_in, model, changes):
    assert signed_in.patch(f"/api/v1/models/{model['id']}", json=changes).status_code == 422


def test_anonymous_cannot_access_models_or_images(client):
    model_id = uuid.uuid4()
    image_id = uuid.uuid4()
    assert client.get("/api/v1/models").status_code == 401
    assert client.post("/api/v1/models", json=PROFILE).status_code == 401
    assert client.get(f"/api/v1/models/{model_id}").status_code == 401
    assert client.get(f"/api/v1/models/{model_id}/images/{image_id}").status_code == 401
    assert upload(client, model_id).status_code == 401


def test_other_account_cannot_read_mutate_or_upload(signed_in, model, db, isolated_storage):
    result = upload(signed_in, model["id"])
    image = result.json()
    other = AuthService(db).create_user(
        f"other-{uuid.uuid4().hex}@example.com", PASSWORD, "另一个用户", "admin"
    )
    signed_in.post("/api/v1/auth/login", json={"email": other.email, "password": PASSWORD})
    assert model["id"] not in [
        item["id"] for item in signed_in.get("/api/v1/models").json()["items"]
    ]
    url = f"/api/v1/models/{model['id']}"
    assert signed_in.get(url).status_code == 404
    assert signed_in.patch(url, json={"name": "stolen"}).status_code == 404
    assert signed_in.delete(url).status_code == 404
    assert upload(signed_in, model["id"]).status_code == 404
    assert signed_in.get(image["image_url"]).status_code == 404
    assert signed_in.delete(image["image_url"]).status_code == 404
    assert len(list(isolated_storage.rglob("*.jpg"))) == 1


@pytest.mark.parametrize(
    "format,extension,mime",
    [
        ("JPEG", "jpg", "image/jpeg"),
        ("PNG", "png", "image/png"),
        ("WEBP", "webp", "image/webp"),
    ],
)
def test_valid_upload_read_and_delete(signed_in, model, format, extension, mime, isolated_storage):
    response = upload(
        signed_in,
        model["id"],
        data=image_bytes(format),
        name=f"../../original.{extension}",
        mime=mime,
    )
    assert response.status_code == 201
    image = response.json()
    assert image["metadata"]["width"] == 96
    assert image["metadata"]["moderation_status"] == "not_screened"
    assert image["metadata"]["rights_confirmed"] is True
    assert "original" not in image["image_url"]
    files = list(isolated_storage.rglob("*.jpg"))
    assert len(files) == 1 and files[0].stem == image["id"]
    served = signed_in.get(image["image_url"])
    assert served.status_code == 200
    assert served.headers["content-type"] == "image/jpeg"
    assert served.headers["cache-control"] == "no-store"
    assert served.headers["x-content-type-options"] == "nosniff"
    with Image.open(io.BytesIO(served.content)) as decoded:
        assert decoded.size == (96, 128)
        assert not decoded.getexif()
    detail = signed_in.get(f"/api/v1/models/{model['id']}").json()
    assert len(detail["reference_images"]) == 1
    assert signed_in.delete(image["image_url"]).status_code == 204
    assert signed_in.get(image["image_url"]).status_code == 404
    assert not list(isolated_storage.rglob("*.jpg"))


@pytest.mark.parametrize(
    "name,mime,data,status",
    [
        ("bad.svg", "image/svg+xml", b"<svg/>", 415),
        ("bad.jpg", "image/png", b"not-image", 415),
        ("bad.jpg", "image/jpeg", image_bytes("PNG"), 415),
        ("bad.png", "image/png", b"not-image", 422),
        ("bad.png", "image/png", b"", 422),
        ("bad.png", "image/png", image_bytes()[:45], 422),
        ("bad.png", "image/png", image_bytes(size=(10, 10)), 422),
    ],
)
def test_invalid_uploads_leave_no_records_or_files(
    signed_in,
    model,
    db,
    isolated_storage,
    name,
    mime,
    data,
    status,
):
    assert upload(signed_in, model["id"], name=name, mime=mime, data=data).status_code == status
    assert db.scalar(select(func.count()).select_from(AIModelImage)) == 0
    assert not list(isolated_storage.rglob("*.jpg"))


def test_upload_requires_declaration(signed_in, model, isolated_storage):
    assert upload(signed_in, model["id"], consent="false").status_code == 422
    assert not list(isolated_storage.rglob("*.jpg"))


def test_upload_size_limit(signed_in, model, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_image_size_mb", 1)
    assert upload(signed_in, model["id"], data=b"x" * (1024 * 1024 + 1)).status_code == 413
    assert upload(signed_in, model["id"], data=b"x" * (2 * 1024 * 1024)).status_code == 413


def test_streamed_request_limit_without_content_length(signed_in, model, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_image_size_mb", 1)

    def chunks():
        yield b'--test\r\nContent-Disposition: form-data; name="file"; filename="x.png"\r\n'
        yield b"Content-Type: image/png\r\n\r\n"
        yield b"x" * (2 * 1024 * 1024)

    response = signed_in.post(
        f"/api/v1/models/{model['id']}/images",
        content=chunks(),
        headers={"Content-Type": "multipart/form-data; boundary=test"},
    )
    assert response.status_code == 413


def test_pixel_and_reference_count_limits(signed_in, model, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_image_pixels", 1024)
    assert upload(signed_in, model["id"]).status_code == 422
    monkeypatch.setattr(get_settings(), "max_image_pixels", 24_000_000)
    monkeypatch.setattr(get_settings(), "max_model_images", 1)
    assert upload(signed_in, model["id"]).status_code == 201
    assert upload(signed_in, model["id"]).status_code == 409


def test_delete_model_cascades_images_and_cleans_files(signed_in, model, db, isolated_storage):
    image = upload(signed_in, model["id"]).json()
    assert signed_in.delete(f"/api/v1/models/{model['id']}").status_code == 204
    assert db.get(AIModel, uuid.UUID(model["id"])) is None
    assert db.scalar(select(func.count()).select_from(AIModelImage)) == 0
    assert signed_in.get(image["image_url"]).status_code == 404
    assert not list(isolated_storage.rglob("*.jpg"))


def test_failed_database_commit_cleans_uploaded_file(
    signed_in, model, db, monkeypatch, isolated_storage
):
    def fail_commit():
        raise SQLAlchemyError("simulated commit failure")

    monkeypatch.setattr(db, "commit", fail_commit)
    assert upload(signed_in, model["id"]).status_code == 503
    assert not list(isolated_storage.rglob("*.jpg"))


def test_failed_storage_write_leaves_no_image(signed_in, model, db, monkeypatch):
    from app.storage.local import LocalImageStorage

    def fail_write(*args):
        raise OSError("simulated storage failure")

    monkeypatch.setattr(LocalImageStorage, "put", fail_write)
    assert upload(signed_in, model["id"]).status_code == 503
    assert db.scalar(select(func.count()).select_from(AIModelImage)) == 0


def test_mutation_csrf_and_missing_ids(signed_in, model):
    assert (
        signed_in.patch(
            f"/api/v1/models/{model['id']}",
            json={"name": "new"},
            headers={"X-Requested-With": ""},
        ).status_code
        == 403
    )
    assert (
        signed_in.delete(
            f"/api/v1/models/{model['id']}",
            headers={
                "Origin": "https://untrusted.example",
            },
        ).status_code
        == 403
    )
    assert signed_in.get(f"/api/v1/models/{uuid.uuid4()}").status_code == 404
    assert signed_in.get("/api/v1/models/not-a-uuid").status_code == 422


def test_private_storage_is_not_static(signed_in, model):
    upload(signed_in, model["id"])
    assert signed_in.get("/storage/models").status_code == 404
    assert signed_in.post(f"/api/v1/models/{model['id']}/generate-reference").status_code == 404


def test_image_orientation_and_metadata_are_normalized(signed_in, model):
    out = io.BytesIO()
    original = Image.new("RGB", (96, 128), "green")
    exif = Image.Exif()
    exif[274] = 6
    exif[315] = "private-test-author"
    original.save(out, format="JPEG", exif=exif)
    response = upload(
        signed_in, model["id"], data=out.getvalue(), name="portrait.jpg", mime="image/jpeg"
    )
    assert response.status_code == 201
    image = response.json()
    assert (image["metadata"]["width"], image["metadata"]["height"]) == (128, 96)
    served = signed_in.get(image["image_url"])
    assert b"private-test-author" not in served.content
    with Image.open(io.BytesIO(served.content)) as normalized:
        assert not normalized.getexif()


def test_options_are_authenticated_and_reflect_limits(client, signed_in, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_model_images", 3)
    assert signed_in.get("/api/v1/models/options").json()["max_model_images"] == 3
    signed_in.post("/api/v1/auth/logout")
    assert client.get("/api/v1/models/options").status_code == 401


def test_storage_rejects_path_escape(isolated_storage):
    from app.storage.local import LocalImageStorage

    storage = LocalImageStorage(isolated_storage)
    with pytest.raises(ValueError):
        storage.put("../outside.jpg", b"not an image")
