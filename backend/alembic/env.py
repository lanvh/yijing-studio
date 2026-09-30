from sqlalchemy import create_engine

from alembic import context
from app.core.config import get_settings
from app.core.database import Base
from app.models import AuthSession, User  # noqa: F401

config = context.config
target_metadata = Base.metadata


def run_on_connection(connection):
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    context.configure(
        url=get_settings().database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    supplied = config.attributes.get("connection")
    if supplied is not None:
        run_on_connection(supplied)
    else:
        engine = create_engine(get_settings().database_url)
        with engine.connect() as connection:
            run_on_connection(connection)
