"""agent lifecycle alert events

Revision ID: 0018_agent_lifecycle_alerts
Revises: 0017_agent_token_pending
Create Date: 2026-08-13
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0018_agent_lifecycle_alerts"
down_revision: str | None = "0017_agent_token_pending"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_lifecycle_alert_events",
        sa.Column(
            "id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "code",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "message",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "resolved_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_agent_lifecycle_alert_events_workspace_id",
        "agent_lifecycle_alert_events",
        ["workspace_id"],
        unique=False,
    )

    op.create_index(
        "ix_agent_lifecycle_alert_events_active",
        "agent_lifecycle_alert_events",
        ["active"],
        unique=False,
    )

    op.create_index(
        "uq_agent_lifecycle_alert_event_active",
        "agent_lifecycle_alert_events",
        ["workspace_id", "code"],
        unique=True,
        postgresql_where=sa.text("active IS TRUE"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_agent_lifecycle_alert_event_active",
        table_name="agent_lifecycle_alert_events",
    )
    op.drop_index(
        "ix_agent_lifecycle_alert_events_active",
        table_name="agent_lifecycle_alert_events",
    )
    op.drop_index(
        "ix_agent_lifecycle_alert_events_workspace_id",
        table_name="agent_lifecycle_alert_events",
    )
    op.drop_table("agent_lifecycle_alert_events")
