"""worker operational state

Revision ID: 0021_worker_operational_state
Revises: 0020_delivery_cursor_indexes
"""

from alembic import op
import sqlalchemy as sa


revision = "0021_worker_operational_state"
down_revision = "0020_delivery_cursor_indexes"
branch_labels = None
depends_on = None


WORKER_NAMES = (
    "backup_scheduler",
    "backup_alert_delivery",
    "agent_lifecycle_alert_delivery",
)


def upgrade() -> None:
    op.create_table(
        "worker_operational_states",
        sa.Column(
            "worker_name",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "last_started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_success_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_failure_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_heartbeat_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_iteration_success",
            sa.Boolean(),
            nullable=True,
        ),
        sa.Column(
            "last_processed_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "last_error",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "worker_name IN ("
            "'backup_scheduler',"
            "'backup_alert_delivery',"
            "'agent_lifecycle_alert_delivery'"
            ")",
            name="ck_worker_operational_state_name",
        ),
        sa.PrimaryKeyConstraint(
            "worker_name",
            name="pk_worker_operational_states",
        ),
    )


def downgrade() -> None:
    op.drop_table("worker_operational_states")
