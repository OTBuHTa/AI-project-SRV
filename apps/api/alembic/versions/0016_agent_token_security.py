"""agent token security

Revision ID: 0016_agent_token_security
Revises: 0015_inventory_lifecycle
Create Date: 2026-08-12
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0016_agent_token_security"
down_revision: str | None = "0015_inventory_lifecycle"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "agents",
        sa.Column(
            "token_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "agents",
        sa.Column(
            "token_rotated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE agents
        SET token_expires_at = created_at + interval '90 days'
        WHERE token_expires_at IS NULL
        """
    )

    op.alter_column(
        "agents",
        "token_expires_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
    op.create_index(
        "ix_agents_token_expires_at",
        "agents",
        ["token_expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_agents_token_expires_at",
        table_name="agents",
    )
    op.drop_column("agents", "token_rotated_at")
    op.drop_column("agents", "token_expires_at")
