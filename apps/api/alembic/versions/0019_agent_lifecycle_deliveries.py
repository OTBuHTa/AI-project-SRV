"""agent lifecycle alert deliveries

Revision ID: 0019_agent_lifecycle_deliveries
Revises: 0018_agent_lifecycle_alerts
"""

from alembic import op
import sqlalchemy as sa


revision = "0019_agent_lifecycle_deliveries"
down_revision = "0018_agent_lifecycle_alerts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_lifecycle_alert_deliveries",
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
            "alert_event_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "channel",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "destination_id",
            sa.String(length=36),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "max_attempts",
            sa.Integer(),
            nullable=False,
            server_default="5",
        ),
        sa.Column(
            "next_attempt_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_attempt_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "delivered_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_error",
            sa.Text(),
            nullable=True,
        ),
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
        sa.ForeignKeyConstraint(
            ["alert_event_id"],
            ["agent_lifecycle_alert_events.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["destination_id"],
            ["notification_destinations.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "alert_event_id",
            "destination_id",
            name=(
                "uq_agent_lifecycle_delivery_"
                "event_destination"
            ),
        ),
    )

    op.create_index(
        "ix_agent_lifecycle_deliveries_workspace_id",
        "agent_lifecycle_alert_deliveries",
        ["workspace_id"],
    )

    op.create_index(
        "ix_agent_lifecycle_deliveries_alert_event_id",
        "agent_lifecycle_alert_deliveries",
        ["alert_event_id"],
    )

    op.create_index(
        "ix_agent_lifecycle_deliveries_destination_id",
        "agent_lifecycle_alert_deliveries",
        ["destination_id"],
    )

    op.create_index(
        "ix_agent_lifecycle_deliveries_status",
        "agent_lifecycle_alert_deliveries",
        ["status"],
    )

    op.create_index(
        "ix_agent_lifecycle_deliveries_next_attempt_at",
        "agent_lifecycle_alert_deliveries",
        ["next_attempt_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_agent_lifecycle_deliveries_next_attempt_at",
        table_name="agent_lifecycle_alert_deliveries",
    )
    op.drop_index(
        "ix_agent_lifecycle_deliveries_status",
        table_name="agent_lifecycle_alert_deliveries",
    )
    op.drop_index(
        "ix_agent_lifecycle_deliveries_destination_id",
        table_name="agent_lifecycle_alert_deliveries",
    )
    op.drop_index(
        "ix_agent_lifecycle_deliveries_alert_event_id",
        table_name="agent_lifecycle_alert_deliveries",
    )
    op.drop_index(
        "ix_agent_lifecycle_deliveries_workspace_id",
        table_name="agent_lifecycle_alert_deliveries",
    )

    op.drop_table(
        "agent_lifecycle_alert_deliveries"
    )
