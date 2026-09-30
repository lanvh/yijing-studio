from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.security import COOKIE_NAME, hash_token, verify_password
from app.models.user import AuthSession
from app.services.auth import AuthService, DuplicateUser
from tests.conftest import PASSWORD


def login(client, user, password=PASSWORD):
    return client.post("/api/v1/auth/login", json={"email": user.email, "password": password})


def test_login_me_logout_revokes_server_session(client, user, db):
    result = login(client, user)
    assert result.status_code == 200
    assert result.json()["email"] == user.email
    assert "password_hash" not in result.json()
    token = client.cookies.get(COOKIE_NAME)
    cookie = result.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie and "path=/api" in cookie
    assert db.get(AuthSession, hash_token(token))
    assert db.get(AuthSession, token) is None
    assert client.get("/api/v1/auth/me").status_code == 200
    assert client.post("/api/v1/auth/logout").status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401
    client.cookies.set(COOKIE_NAME, token)
    assert client.get("/api/v1/auth/me").status_code == 401


@pytest.mark.parametrize("password", ["wrong-password", ""])
def test_wrong_password(client, user, password):
    assert login(client, user, password).status_code in {401, 422}


def test_unknown_and_disabled_are_indistinguishable(client, user, db):
    result = client.post(
        "/api/v1/auth/login",
        json={
            "email": "missing@example.com",
            "password": PASSWORD,
        },
    )
    user.enabled = False
    db.commit()
    disabled = login(client, user)
    assert disabled.status_code == result.status_code == 401
    assert disabled.json() == result.json()


def test_disabled_user_existing_session(client, user, db):
    login(client, user)
    user.enabled = False
    db.commit()
    assert client.get("/api/v1/auth/me").status_code == 401


def test_expired_session(client, user, db):
    login(client, user)
    session = db.get(AuthSession, hash_token(client.cookies.get(COOKIE_NAME)))
    session.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db.commit()
    assert client.get("/api/v1/auth/me").status_code == 401


def test_anonymous_and_tampered_session(client):
    assert client.get("/api/v1/auth/me").status_code == 401
    client.cookies.set(COOKIE_NAME, "tampered")
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.post("/api/v1/auth/logout").status_code == 204


def test_login_rotates_session(client, user, db):
    login(client, user)
    first = client.cookies.get(COOKIE_NAME)
    login(client, user)
    assert client.cookies.get(COOKIE_NAME) != first
    assert db.get(AuthSession, hash_token(first)) is None


def test_uppercase_email(client, user):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email.upper(),
            "password": PASSWORD,
        },
    )
    assert response.status_code == 200


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "bad", "password": PASSWORD},
        {"email": "test@example.com"},
        {"email": "test@example.com", "password": "x" * 129},
    ],
)
def test_validation(client, payload):
    assert client.post("/api/v1/auth/login", json=payload).status_code == 422


@pytest.mark.parametrize("path", ["/api/v1/auth/login", "/api/v1/auth/logout"])
def test_csrf_requires_header_and_trusted_origin(client, user, path):
    payload = {"email": user.email, "password": PASSWORD}
    assert (
        client.post(
            path,
            json=payload,
            headers={
                "X-Requested-With": "",
            },
        ).status_code
        == 403
    )
    assert (
        client.post(
            path,
            json=payload,
            headers={
                "Origin": "https://untrusted.example",
            },
        ).status_code
        == 403
    )


def test_no_public_registration(client):
    assert client.post("/api/v1/auth/register", json={}).status_code == 404


def test_create_account_hashes_password_and_rejects_duplicate(db, user):
    assert user.password_hash != PASSWORD
    assert verify_password(PASSWORD, user.password_hash)
    with pytest.raises(DuplicateUser):
        AuthService(db).create_user(user.email.upper(), PASSWORD, "重复", "user")


def test_weak_password_rejected(db):
    with pytest.raises(ValueError):
        AuthService(db).create_user("weak@example.com", "short", "弱密码", "user")


def test_readiness(client):
    assert client.get("/api/v1/health/ready").json()["database"] == "ready"


def test_cookie_secure_setting(client, user, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "cookie_secure", True)
    assert "Secure" in login(client, user).headers["set-cookie"]


def test_failed_login_creates_no_session(client, user, db):
    login(client, user, "incorrect")
    assert db.scalar(select(AuthSession).where(AuthSession.user_id == user.id)) is None
