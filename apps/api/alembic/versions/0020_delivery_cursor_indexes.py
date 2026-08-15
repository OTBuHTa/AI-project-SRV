"""notification delivery cursor indexes

Revision ID: 0020_delivery_cursor_indexes
Revises: 0019_agent_lifecycle_deliveries
"""

from alembic import op


revision = "0020_delivery_cursor_indexes"
down_revision = "0019_agent_lifecycle_deliveries"
branch_labels = None
depends_on = None


BACKUP_INDEX = (
    "ix_backup_alert_deliveries_workspace_created_id"
)

LIFECYCLE_INDEX = (
    "ix_agent_lifecycle_deliveries_workspace_created_id"
)


def upgrade() -> None:
    op.create_index(
        BACKUP_INDEX,
        "backup_alert_deliveries",
        [
            "workspace_id",
            "created_at",
            "id",
        ],
        unique=False,
    )

    op.create_index(
        LIFECYCLE_INDEX,
        "agent_lifecycle_alert_deliveries",
        [
            "workspace_id",
            "created_at",
            "id",
        ],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        LIFECYCLE_INDEX,
        table_name="agent_lifecycle_alert_deliveries",
    )

    op.drop_index(
        BACKUP_INDEX,
        table_name="backup_alert_deliveries",
    )
