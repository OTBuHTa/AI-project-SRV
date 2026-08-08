"""backup alert active partial uniqueness

Revision ID: 0010_backup_alert_active_unique
Revises: 0009_backup_alert_events
"""

from alembic import op


revision = "0010_backup_alert_active_unique"
down_revision = "0009_backup_alert_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_backup_alert_event_active",
        "backup_alert_events",
        type_="unique",
    )

    op.execute(
        """
        CREATE UNIQUE INDEX uq_backup_alert_event_active
        ON backup_alert_events (workspace_id, code)
        WHERE active IS TRUE
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS uq_backup_alert_event_active
        """
    )

    op.create_unique_constraint(
        "uq_backup_alert_event_active",
        "backup_alert_events",
        ["workspace_id", "code", "active"],
    )
