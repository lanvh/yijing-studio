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
            assert {"users", "auth_sessions", "alembic_version"} <= set(tables)
            command.check(config)
            command.downgrade(config, "base")
            assert inspect(connection).get_table_names(schema=schema) == ["alembic_version"]
        finally:
            transaction.rollback()
