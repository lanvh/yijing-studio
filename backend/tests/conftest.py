import uuid

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from alembic import command
from app.core.database import engine, get_db
from app.main import app
from app.services.auth import AuthService

PASSWORD = "Test-only-password-123!"


@pytest.fixture(scope="session")
def migrated_database():
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def db(migrated_database):
    with engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
            yield session
        transaction.rollback()


@pytest.fixture
def user(db):
    return AuthService(db).create_user(
        f"test-{uuid.uuid4().hex}@example.com", PASSWORD, "测试创作者", "user"
    )


@pytest.fixture
def client(db):
    def override():
        yield db

    app.dependency_overrides[get_db] = override
    with TestClient(app, headers={"X-Requested-With": "AISeedStudio"}) as http:
        yield http
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def no_paid_services_in_tests(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "image_provider", "mock")
    monkeypatch.setattr(get_settings(), "llm_provider", "local")
