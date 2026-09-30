import io
import uuid

import pytest
from PIL import Image
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.models.product import ProductImage
from app.schemas.product import CATEGORIES
from app.services.auth import AuthService
from app.storage.local import LocalImageStorage
from tests.conftest import PASSWORD

PROFILE = {"name": "白色运动鞋", "category": "shoes", "color": "白色", "brand": "测试品牌"}


def picture(format="PNG"):
    out = io.BytesIO()
    image = Image.new("RGB", (96, 128), "white")
    if format == "JPEG":
        exif = Image.Exif()
        exif[274] = 6
        exif[315] = "private-author"
        image.save(out, format=format, exif=exif)
    else:
        image.save(out, format=format)
    return out.getvalue()


@pytest.fixture(autouse=True)
def storage(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "local_storage_path", str(tmp_path))
    return tmp_path


@pytest.fixture
def signed(client, user):
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
def product(signed):
    response = signed.post("/api/v1/products", json=PROFILE)
    assert response.status_code == 201
    return response.json()


def upload(signed, product, data=None, name="product.png", mime="image/png", consent="true"):
    return signed.post(
        f"/api/v1/products/{product['id']}/images",
        files={"file": (name, picture() if data is None else data, mime)},
        data={"rights_confirmed": consent},
    )


def files(storage):
    return [p for p in storage.rglob("*") if p.is_file()]


@pytest.mark.parametrize("category", CATEGORIES)
def test_supported_categories(signed, category):
    response = signed.post("/api/v1/products", json={**PROFILE, "category": category})
    assert response.status_code == 201
    assert response.json()["product_features"]["category"] == category


def test_crud_and_attributed_features(signed, product):
    url = "/api/v1/products/" + product["id"]
    features = product["product_features"]
    assert features["material_guess"] is None
    assert features["material"] is None
    assert features["image_observations"] == []
    assert features["sources"]["product_fields"] == "user_provided"
    changed = signed.patch(
        url,
        json={
            "brand": "",
            "category": "bag",
            "feature_notes": {
                "material": "棉",
                "shape": "方形",
                "critical_features": ["双提手"],
            },
        },
    )
    assert changed.status_code == 200
    changed = signed.patch(url, json={"feature_notes": {"pattern": "条纹"}}).json()
    assert changed["product_features"]["material"] == "棉"
    assert changed["product_features"]["pattern"] == "条纹"
    assert changed["product_features"]["brand"] is None
    assert signed.post(url + "/analyze").json()["product_features"]["shape"] == "方形"
    assert signed.get(url).json()["category"] == "bag"
    assert signed.delete(url).status_code == 204
    assert signed.get(url).status_code == 404


def test_filters_pagination_and_literal_search(signed):
    for i, category in enumerate(["top", "shoes", "top"]):
        signed.post(
            "/api/v1/products",
            json={
                **PROFILE,
                "category": category,
                "name": f"100%商品{i}",
                "brand": "品牌检索",
            },
        )
    result = signed.get(
        "/api/v1/products",
        params={
            "q": "品牌检索",
            "category": "top",
            "limit": 1,
            "offset": 1,
        },
    ).json()
    assert result["total"] == 2 and len(result["items"]) == 1
    assert signed.get("/api/v1/products", params={"q": "100%"}).json()["total"] == 3
    assert signed.get("/api/v1/products", params={"q": "100_"}).json()["total"] == 0
    assert signed.get("/api/v1/products?category=invalid").status_code == 422


@pytest.mark.parametrize(
    "changes",
    [
        {"name": " "},
        {"category": "invalid"},
        {"brand": None},
        {"name": "x" * 101},
        {"product_features": {"brand": "invented"}},
        {"user_id": str(uuid.uuid4())},
        {"feature_notes": {"material_guess": "invented"}},
        {"feature_notes": None},
    ],
)
def test_validation(signed, product, changes):
    assert signed.post("/api/v1/products", json={**PROFILE, **changes}).status_code == 422
    assert signed.patch("/api/v1/products/" + product["id"], json=changes).status_code == 422


@pytest.mark.parametrize(
    "format,extension,mime",
    [
        ("JPEG", "jpg", "image/jpeg"),
        ("PNG", "png", "image/png"),
        ("WEBP", "webp", "image/webp"),
    ],
)
def test_original_preview_and_pair_removal(signed, product, storage, format, extension, mime):
    raw = picture(format)
    response = upload(signed, product, raw, "../../product." + extension, mime)
    assert response.status_code == 201
    result = response.json()
    original, processed = result["original_images"][0], result["processed_images"][0]
    assert len(files(storage)) == 2
    downloaded = signed.get(original["image_url"])
    assert downloaded.content == raw
    assert downloaded.headers["content-disposition"].startswith("attachment;")
    preview = signed.get(processed["image_url"])
    assert preview.headers["content-type"] == "image/jpeg"
    assert preview.headers["cache-control"] == "no-store"
    assert preview.headers["x-content-type-options"] == "nosniff"
    assert b"private-author" not in preview.content
    with Image.open(io.BytesIO(preview.content)) as image:
        assert not image.getexif()
        assert image.size == ((128, 96) if format == "JPEG" else (96, 128))
    features = result["product_features"]
    assert features["image_observations"][0]["palette"]
    assert features["color"] == ["白色"]
    assert features["material_guess"] is None
    removed = signed.delete(processed["image_url"])
    assert removed.status_code == 200
    assert removed.json()["original_images"] == removed.json()["processed_images"] == []
    assert removed.json()["product_features"]["image_observations"] == []
    assert signed.get(original["image_url"]).status_code == 404
    assert files(storage) == []


def test_account_isolation(signed, product, db, storage):
    result = upload(signed, product).json()
    other = AuthService(db).create_user(
        f"other-{uuid.uuid4().hex}@example.com", PASSWORD, "Other", "admin"
    )
    signed.post("/api/v1/auth/login", json={"email": other.email, "password": PASSWORD})
    url = "/api/v1/products/" + product["id"]
    assert signed.get("/api/v1/products").json()["total"] == 0
    assert signed.get(url).status_code == 404
    assert signed.patch(url, json={"name": "stolen"}).status_code == 404
    assert signed.delete(url).status_code == 404
    assert signed.post(url + "/analyze").status_code == 404
    assert upload(signed, product).status_code == 404
    for image in result["original_images"] + result["processed_images"]:
        assert signed.get(image["image_url"]).status_code == 404
        assert signed.delete(image["image_url"]).status_code == 404
    assert len(files(storage)) == 2


def test_anonymous_and_csrf(client, signed, product):
    url = "/api/v1/products/" + product["id"]
    assert signed.post(url + "/analyze", headers={"X-Requested-With": ""}).status_code == 403
    assert signed.delete(url, headers={"Origin": "https://invalid.example"}).status_code == 403
    signed.post("/api/v1/auth/logout")
    assert client.get("/api/v1/products").status_code == 401
    assert client.get("/api/v1/products/options").status_code == 401
    assert client.get(url).status_code == 401
    assert client.post("/api/v1/products", json=PROFILE).status_code == 401
    assert upload(client, product).status_code == 401


def test_limits_and_invalid_uploads(signed, product, storage, monkeypatch):
    assert upload(signed, product, consent="false").status_code == 422
    assert upload(signed, product, data=b"invalid").status_code == 422
    assert upload(signed, product, name="bad.jpg").status_code == 415
    monkeypatch.setattr(get_settings(), "max_image_size_mb", 1)
    assert upload(signed, product, data=b"x" * (2 * 1024 * 1024)).status_code == 413
    assert files(storage) == []
    monkeypatch.setattr(get_settings(), "max_product_images", 1)
    assert signed.get("/api/v1/products/options").json()["max_product_images"] == 1
    assert upload(signed, product).status_code == 201
    assert upload(signed, product).status_code == 409


def test_delete_product_cleans_both_files(signed, product, db, storage):
    upload(signed, product)
    assert signed.delete("/api/v1/products/" + product["id"]).status_code == 204
    assert files(storage) == []
    assert (
        db.scalar(
            select(func.count())
            .select_from(ProductImage)
            .where(ProductImage.product_id == uuid.UUID(product["id"]))
        )
        == 0
    )


def test_second_file_failure_cleans_first(signed, product, db, storage, monkeypatch):
    real_put = LocalImageStorage.put
    calls = 0

    def fail_second(self, key, data):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated preview write failure")
        real_put(self, key, data)

    monkeypatch.setattr(LocalImageStorage, "put", fail_second)
    assert upload(signed, product).status_code == 503
    assert files(storage) == []
    assert (
        db.scalar(
            select(func.count())
            .select_from(ProductImage)
            .where(ProductImage.product_id == uuid.UUID(product["id"]))
        )
        == 0
    )


def test_commit_failure_cleans_both_files(signed, product, db, storage, monkeypatch):
    def fail_commit():
        raise SQLAlchemyError("simulated commit failure")

    monkeypatch.setattr(db, "commit", fail_commit)
    assert upload(signed, product).status_code == 503
    assert files(storage) == []


def test_chunked_product_upload_limit(signed, product, monkeypatch, storage):
    monkeypatch.setattr(get_settings(), "max_image_size_mb", 1)

    def chunks():
        yield b'--test\r\nContent-Disposition: form-data; name="file"; filename="x.png"\r\n'
        yield b"Content-Type: image/png\r\n\r\n"
        yield b"x" * (2 * 1024 * 1024)

    response = signed.post(
        f"/api/v1/products/{product['id']}/images",
        content=chunks(),
        headers={"Content-Type": "multipart/form-data; boundary=test"},
    )
    assert response.status_code == 413
    assert files(storage) == []
