"""backup pipeline

Revision ID: 0007_backup_pipeline
Revises: 0006_ai_action_verification
"""

from alembic import op
import sqlalchemy as sa

revision = "0007_backup_pipeline"
down_revision = "0006_ai_action_verification"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "backup_jobs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("workspace_id", sa.String(), nullable=False, index=True),
        sa.Column("backup_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="created"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "backup_artifacts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("backup_job_id", sa.String(), nullable=False, index=True),
        sa.Column("artifact_type", sa.String(), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("storage_uri", sa.Text(), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="created"),
        sa.Column("restore_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_table("backup_artifacts")
    op.drop_table("backup_jobs")
