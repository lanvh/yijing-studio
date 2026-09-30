import uuid

from alembic.config import Config
from sqlalchemy import inspect, text

from alembic import command
from app.core.database import engine


def test_migration_upgrade_downgrade_in_isolated_schema():
    schema = "migration_test_" + uuid.uuid4().hex
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            config = Config("alembic.ini")
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
            tables = inspect(connection).get_table_names(schema=schema)
            assert {
                "users",
                "auth_sessions",
                "ai_models",
                "ai_model_images",
                "alembic_version",
                "products",
                "product_images",
                "generation_tasks",
                "generation_results",
                "content_copy",
            } <= set(tables)
            command.check(config)
            command.downgrade(config, "base")
            assert inspect(connection).get_table_names(schema=schema) == ["alembic_version"]
        finally:
            transaction.rollback()


def test_phase2_migration_preserves_existing_users():
    schema = "phase2_migration_" + uuid.uuid4().hex
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            config = Config("alembic.ini")
            config.attributes["connection"] = connection
            command.upgrade(config, "0001")
            connection.execute(
                text(
                    "INSERT INTO users (id, email, password_hash, display_name, role, enabled) "
                    "VALUES (:id, 'migration@example.com', 'test-hash', 'Existing', 'user', true)"
                ),
                {"id": uuid.uuid4()},
            )
            command.upgrade(config, "head")
            assert connection.scalar(text("SELECT count(*) FROM users")) == 1
            command.downgrade(config, "0001")
            assert connection.scalar(text("SELECT count(*) FROM users")) == 1
            assert "ai_models" not in inspect(connection).get_table_names(schema=schema)
            command.upgrade(config, "head")
            command.check(config)
        finally:
            transaction.rollback()


def test_phase3_migration_preserves_models_and_images():
    schema = "phase3_migration_" + uuid.uuid4().hex
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            config = Config("alembic.ini")
            config.attributes["connection"] = connection
            command.upgrade(config, "0002")
            user_id, model_id, image_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
            connection.execute(
                text(
                    "INSERT INTO users (id, email, password_hash, display_name, role, enabled) "
                    "VALUES (:id, 'existing@example.com', 'hash', 'Existing', 'user', true)"
                ),
                {"id": user_id},
            )
            connection.execute(
                text(
                    "INSERT INTO ai_models (id,user_id,name,gender,age_range,body_type,skin_tone,"
                    "hair_style,hair_color,style,description,character_prompt,negative_prompt,"
                    "provider_metadata) VALUES (:id,:user,'Existing','female','25-34',"
                    "'','','','','','','','','{}')"
                ),
                {"id": model_id, "user": user_id},
            )
            connection.execute(
                text(
                    "INSERT INTO ai_model_images (id,model_id,image_url,image_type,metadata) "
                    "VALUES (:id,:model,'/existing.jpg','reference','{}')"
                ),
                {"id": image_id, "model": model_id},
            )
            for revision in ["head", "0002", "head"]:
                command.upgrade(config, revision) if revision == "head" else command.downgrade(
                    config, revision
                )
                assert connection.scalar(text("SELECT count(*) FROM users")) == 1
                assert connection.scalar(text("SELECT name FROM ai_models")) == "Existing"
                assert connection.scalar(text("SELECT image_url FROM ai_model_images")) == (
                    "/existing.jpg"
                )
            command.check(config)
        finally:
            transaction.rollback()
