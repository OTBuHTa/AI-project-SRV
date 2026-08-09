"""resource inventory

Revision ID: 0014_resource_inventory
Revises: 0013_delivery_destination
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0014_resource_inventory"
down_revision = "0013_delivery_destination"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "resource_inventory_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "resource_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "kind",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "external_id",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="unknown",
        ),
        sa.Column(
            "attributes",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "observed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
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
            ["workspace_id"],
            ["workspaces.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["resource_id"],
            ["resources.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "resource_id",
            "kind",
            "external_id",
            name="uq_resource_inventory_identity",
        ),
    )

    op.create_index(
        "ix_resource_inventory_workspace_id",
        "resource_inventory_items",
        ["workspace_id"],
    )

    op.create_index(
        "ix_resource_inventory_resource_id",
        "resource_inventory_items",
        ["resource_id"],
    )

    op.create_index(
        "ix_resource_inventory_kind",
        "resource_inventory_items",
        ["kind"],
    )

    op.create_index(
        "ix_resource_inventory_status",
        "resource_inventory_items",
        ["status"],
    )

    op.create_index(
        "ix_resource_inventory_observed_at",
        "resource_inventory_items",
        ["observed_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_resource_inventory_observed_at",
        table_name="resource_inventory_items",
    )
    op.drop_index(
        "ix_resource_inventory_status",
        table_name="resource_inventory_items",
    )
    op.drop_index(
        "ix_resource_inventory_kind",
        table_name="resource_inventory_items",
    )
    op.drop_index(
        "ix_resource_inventory_resource_id",
        table_name="resource_inventory_items",
    )
    op.drop_index(
        "ix_resource_inventory_workspace_id",
        table_name="resource_inventory_items",
    )

    op.drop_table("resource_inventory_items")
