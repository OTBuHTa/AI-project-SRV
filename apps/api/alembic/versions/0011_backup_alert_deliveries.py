"""backup alert deliveries

Revision ID: 0011_backup_alert_deliveries
Revises: 0010_backup_alert_active_unique
"""

from alembic import op
import sqlalchemy as sa


revision = "0011_backup_alert_deliveries"
down_revision = "0010_backup_alert_active_unique"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "backup_alert_deliveries",
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
            ["backup_alert_events.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "alert_event_id",
            "channel",
            name="uq_backup_alert_delivery_event_channel",
        ),
    )

    op.create_index(
        "ix_backup_alert_deliveries_workspace_id",
        "backup_alert_deliveries",
        ["workspace_id"],
    )

    op.create_index(
        "ix_backup_alert_deliveries_alert_event_id",
        "backup_alert_deliveries",
        ["alert_event_id"],
    )

    op.create_index(
        "ix_backup_alert_deliveries_status",
        "backup_alert_deliveries",
        ["status"],
    )

    op.create_index(
        "ix_backup_alert_deliveries_next_attempt_at",
        "backup_alert_deliveries",
        ["next_attempt_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_backup_alert_deliveries_next_attempt_at",
        table_name="backup_alert_deliveries",
    )
    op.drop_index(
        "ix_backup_alert_deliveries_status",
        table_name="backup_alert_deliveries",
    )
    op.drop_index(
        "ix_backup_alert_deliveries_alert_event_id",
        table_name="backup_alert_deliveries",
    )
    op.drop_index(
        "ix_backup_alert_deliveries_workspace_id",
        table_name="backup_alert_deliveries",
    )

    op.drop_table("backup_alert_deliveries")
