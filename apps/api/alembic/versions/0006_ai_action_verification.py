"""AI action proposals and post-execution verification
Revision ID: 0006_ai_action_verification
Revises: 0005_action_policy_approval
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_ai_action_verification"
down_revision = "0005_action_policy_approval"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("action_plans", sa.Column("source", sa.String(32), nullable=False, server_default="manual"))
    op.add_column("action_plans", sa.Column("verification_status", sa.String(32), nullable=True))
    op.add_column("action_plans", sa.Column("verification_result", postgresql.JSONB(), nullable=True))
    op.add_column("action_plans", sa.Column("verification_started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("action_plans", sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column("action_plans", "verified_at")
    op.drop_column("action_plans", "verification_started_at")
    op.drop_column("action_plans", "verification_result")
    op.drop_column("action_plans", "verification_status")
    op.drop_column("action_plans", "source")
