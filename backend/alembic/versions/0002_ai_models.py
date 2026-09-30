"""AI model profiles and private reference images."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_models",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("gender", sa.String(32), nullable=False),
        sa.Column("age_range", sa.String(32), nullable=False),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("body_type", sa.String(60), nullable=False),
        sa.Column("skin_tone", sa.String(60), nullable=False),
        sa.Column("hair_style", sa.String(80), nullable=False),
        sa.Column("hair_color", sa.String(60), nullable=False),
        sa.Column("style", sa.String(80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("character_prompt", sa.Text(), nullable=False),
        sa.Column("negative_prompt", sa.Text(), nullable=False),
        sa.Column("provider_metadata", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "height IS NULL OR (height >= 100 AND height <= 250)", name="ck_model_height"
        ),
        sa.CheckConstraint(
            "age_range IN ('18-24','25-34','35-44','45-54','55+')", name="ck_model_adult_age"
        ),
    )
    op.create_index("ix_ai_models_user_id", "ai_models", ["user_id"])
    op.create_table(
        "ai_model_images",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "model_id", sa.Uuid(), sa.ForeignKey("ai_models.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("image_url", sa.Text(), nullable=False),
        sa.Column("image_type", sa.String(32), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_ai_model_images_model_id", "ai_model_images", ["model_id"])


def downgrade():
    op.drop_table("ai_model_images")
    op.drop_table("ai_models")
