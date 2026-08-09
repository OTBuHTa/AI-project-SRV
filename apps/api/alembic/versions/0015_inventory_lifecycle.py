"""inventory lifecycle

Revision ID: 0015_inventory_lifecycle
Revises: 0014_resource_inventory
"""

from alembic import op
import sqlalchemy as sa


revision = "0015_inventory_lifecycle"
down_revision = "0014_resource_inventory"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "resource_inventory_items",
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "resource_inventory_items",
        sa.Column(
            "lifecycle_status",
            sa.String(length=32),
            nullable=False,
            server_default="observed",
        ),
    )

    op.create_index(
        "ix_resource_inventory_last_seen_at",
        "resource_inventory_items",
        ["last_seen_at"],
    )

    op.create_index(
        "ix_resource_inventory_lifecycle_status",
        "resource_inventory_items",
        ["lifecycle_status"],
    )

    op.execute(
        """
        UPDATE resource_inventory_items
        SET last_seen_at = observed_at
        WHERE last_seen_at IS NULL
        """
    )


def downgrade() -> None:
    op.drop_index(
        "ix_resource_inventory_lifecycle_status",
        table_name="resource_inventory_items",
    )

    op.drop_index(
        "ix_resource_inventory_last_seen_at",
        table_name="resource_inventory_items",
    )

    op.drop_column(
        "resource_inventory_items",
        "lifecycle_status",
    )

    op.drop_column(
        "resource_inventory_items",
        "last_seen_at",
    )
