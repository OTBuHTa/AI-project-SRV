"""notification routing

Revision ID: 0012_notification_routing
Revises: 0011_backup_alert_deliveries
"""

from alembic import op
import sqlalchemy as sa


revision = "0012_notification_routing"
down_revision = "0011_backup_alert_deliveries"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_destinations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column(
            "channel",
            sa.String(length=32),
            nullable=False,
            server_default="webhook",
        ),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id",
            "name",
            name="uq_notification_destination_workspace_name",
        ),
    )

    op.create_index(
        "ix_notification_destinations_workspace_id",
        "notification_destinations",
        ["workspace_id"],
    )

    op.create_index(
        "ix_notification_destinations_enabled",
        "notification_destinations",
        ["enabled"],
    )

    op.create_table(
        "notification_routes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("destination_id", sa.String(length=36), nullable=False),
        sa.Column("alert_code", sa.String(length=64), nullable=True),
        sa.Column("severity", sa.String(length=32), nullable=True),
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
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
            ["destination_id"],
            ["notification_destinations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_notification_routes_workspace_id",
        "notification_routes",
        ["workspace_id"],
    )

    op.create_index(
        "ix_notification_routes_destination_id",
        "notification_routes",
        ["destination_id"],
    )

    op.create_index(
        "ix_notification_routes_enabled",
        "notification_routes",
        ["enabled"],
    )

    op.add_column(
        "backup_alert_deliveries",
        sa.Column(
            "destination_id",
            sa.String(length=36),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_backup_alert_deliveries_destination",
        "backup_alert_deliveries",
        "notification_destinations",
        ["destination_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_index(
        "ix_backup_alert_deliveries_destination_id",
        "backup_alert_deliveries",
        ["destination_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_backup_alert_deliveries_destination_id",
        table_name="backup_alert_deliveries",
    )

    op.drop_constraint(
        "fk_backup_alert_deliveries_destination",
        "backup_alert_deliveries",
        type_="foreignkey",
    )

    op.drop_column(
        "backup_alert_deliveries",
        "destination_id",
    )

    op.drop_index(
        "ix_notification_routes_enabled",
        table_name="notification_routes",
    )
    op.drop_index(
        "ix_notification_routes_destination_id",
        table_name="notification_routes",
    )
    op.drop_index(
        "ix_notification_routes_workspace_id",
        table_name="notification_routes",
    )
    op.drop_table("notification_routes")

    op.drop_index(
        "ix_notification_destinations_enabled",
        table_name="notification_destinations",
    )
    op.drop_index(
        "ix_notification_destinations_workspace_id",
        table_name="notification_destinations",
    )
    op.drop_table("notification_destinations")
