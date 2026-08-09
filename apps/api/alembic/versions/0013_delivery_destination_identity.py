"""delivery destination identity

Revision ID: 0013_delivery_destination
Revises: 0012_notification_routing
"""

from alembic import op


revision = "0013_delivery_destination"
down_revision = "0012_notification_routing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_backup_alert_delivery_event_channel",
        "backup_alert_deliveries",
        type_="unique",
    )

    op.create_unique_constraint(
        "uq_backup_alert_delivery_event_destination",
        "backup_alert_deliveries",
        ["alert_event_id", "destination_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_backup_alert_delivery_event_destination",
        "backup_alert_deliveries",
        type_="unique",
    )

    op.create_unique_constraint(
        "uq_backup_alert_delivery_event_channel",
        "backup_alert_deliveries",
        ["alert_event_id", "channel"],
    )
