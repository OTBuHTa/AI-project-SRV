"""backup scheduling

Revision ID: 0008_backup_scheduling
Revises: 0007_backup_pipeline
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_backup_scheduling"
down_revision = "0007_backup_pipeline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "backup_schedules",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "interval_minutes",
            sa.Integer(),
            nullable=False,
            server_default="1440",
        ),
        sa.Column(
            "retention_keep_last",
            sa.Integer(),
            nullable=False,
            server_default="7",
        ),
        sa.Column(
            "retention_max_age_days",
            sa.Integer(),
            nullable=False,
            server_default="30",
        ),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_backup_schedules_workspace_id",
        "backup_schedules",
        ["workspace_id"],
        unique=True,
    )

    op.create_index(
        "ix_backup_schedules_next_run_at",
        "backup_schedules",
        ["next_run_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_backup_schedules_next_run_at",
        table_name="backup_schedules",
    )
    op.drop_index(
        "ix_backup_schedules_workspace_id",
        table_name="backup_schedules",
    )
    op.drop_table("backup_schedules")
