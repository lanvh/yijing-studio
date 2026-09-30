"""generation_workflow"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "generation_tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("model_id", sa.Uuid(), nullable=True),
        sa.Column("product_id", sa.Uuid(), nullable=True),
        sa.Column("request_key", sa.Uuid(), nullable=False),
        sa.Column("scene", sa.String(length=32), nullable=False),
        sa.Column("style", sa.String(length=32), nullable=False),
        sa.Column("pose", sa.String(length=32), nullable=False),
        sa.Column("requested_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("provider_job_id", sa.String(length=256), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("negative_prompt", sa.Text(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('PENDING','PROCESSING','SUCCEEDED','PARTIAL','FAILED')",
            name="ck_task_status",
        ),
        sa.CheckConstraint("requested_count IN (1,2,4,6)", name="ck_task_count"),
        sa.ForeignKeyConstraint(["model_id"], ["ai_models.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "request_key", name="uq_task_request"),
    )
    op.create_index(
        op.f("ix_generation_tasks_user_id"), "generation_tasks", ["user_id"], unique=False
    )
    op.create_table(
        "content_copy",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("caption", sa.Text(), nullable=False),
        sa.Column("hashtags", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("product_summary", sa.Text(), nullable=False),
        sa.Column("styling_notes", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["task_id"], ["generation_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id"),
    )
    op.create_table(
        "generation_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("identity_score", sa.Float(), nullable=True),
        sa.Column("product_score", sa.Float(), nullable=True),
        sa.Column("anatomy_score", sa.Float(), nullable=True),
        sa.Column("aesthetic_score", sa.Float(), nullable=True),
        sa.Column("is_selected", sa.Boolean(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["task_id"], ["generation_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_generation_results_task_id"), "generation_results", ["task_id"], unique=False
    )


def downgrade():
    op.drop_index(op.f("ix_generation_results_task_id"), table_name="generation_results")
    op.drop_table("generation_results")
    op.drop_table("content_copy")
    op.drop_index(op.f("ix_generation_tasks_user_id"), table_name="generation_tasks")
    op.drop_table("generation_tasks")
