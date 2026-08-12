"""agent pending token rotation

Revision ID: 0017_agent_token_pending
Revises: 0016_agent_token_security
Create Date: 2026-08-12
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0017_agent_token_pending"
down_revision: str | None = "0016_agent_token_security"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "agents",
        sa.Column(
            "pending_token_hash",
            sa.String(length=128),
            nullable=True,
        ),
    )
    op.add_column(
        "agents",
        sa.Column(
            "pending_token_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "agents",
        sa.Column(
            "token_rotation_prepared_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_agents_pending_token_hash",
        "agents",
        ["pending_token_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_agents_pending_token_hash",
        table_name="agents",
    )
    op.drop_column(
        "agents",
        "token_rotation_prepared_at",
    )
    op.drop_column(
        "agents",
        "pending_token_expires_at",
    )
    op.drop_column(
        "agents",
        "pending_token_hash",
    )
