"""backup alert events

Revision ID: 0009_backup_alert_events
Revises: 0008_backup_scheduling
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_backup_alert_events"
down_revision = "0008_backup_scheduling"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "backup_alert_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
        sa.Column("acknowledged_by", sa.String(length=36)),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_backup_alert_events_workspace_id",
        "backup_alert_events",
        ["workspace_id"],
    )

    op.create_index(
        "ix_backup_alert_events_active",
        "backup_alert_events",
        ["active"],
    )

    op.create_unique_constraint(
        "uq_backup_alert_event_active",
        "backup_alert_events",
        ["workspace_id", "code", "active"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_backup_alert_event_active",
        "backup_alert_events",
        type_="unique",
    )
    op.drop_index(
        "ix_backup_alert_events_active",
        table_name="backup_alert_events",
    )
    op.drop_index(
        "ix_backup_alert_events_workspace_id",
        table_name="backup_alert_events",
    )
    op.drop_table("backup_alert_events")
