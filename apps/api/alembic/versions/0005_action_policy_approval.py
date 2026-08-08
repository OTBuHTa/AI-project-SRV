"""Action plans, approval and agent tasks
Revision ID: 0005_action_policy_approval
Revises: 0004_ai_conversations
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="0005_action_policy_approval"
down_revision="0004_ai_conversations"
branch_labels=None
depends_on=None

def upgrade():
    op.create_table("action_plans",
        sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
        sa.Column("workspace_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("workspaces.id",ondelete="CASCADE"),nullable=False),
        sa.Column("user_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False),
        sa.Column("resource_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("resources.id",ondelete="CASCADE"),nullable=False),
        sa.Column("capability",sa.String(120),nullable=False),sa.Column("parameters",postgresql.JSONB(),nullable=False),
        sa.Column("rationale",sa.Text()),sa.Column("risk_level",sa.Integer(),nullable=False),
        sa.Column("requires_approval",sa.Boolean(),nullable=False),sa.Column("status",sa.String(32),nullable=False),
        sa.Column("approved_by_user_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("users.id")),sa.Column("approved_at",sa.DateTime(timezone=True)),
        sa.Column("completed_at",sa.DateTime(timezone=True)),sa.Column("result",postgresql.JSONB()),
        sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False))
    for col in ("workspace_id","user_id","resource_id","capability","status"):
        op.create_index(f"ix_action_plans_{col}","action_plans",[col])
    op.create_table("agent_tasks",
        sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
        sa.Column("workspace_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("workspaces.id",ondelete="CASCADE"),nullable=False),
        sa.Column("action_plan_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("action_plans.id",ondelete="CASCADE"),nullable=False),
        sa.Column("agent_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("agents.id",ondelete="CASCADE"),nullable=False),
        sa.Column("capability",sa.String(120),nullable=False),sa.Column("parameters",postgresql.JSONB(),nullable=False),
        sa.Column("status",sa.String(32),nullable=False),sa.Column("lease_expires_at",sa.DateTime(timezone=True)),
        sa.Column("started_at",sa.DateTime(timezone=True)),sa.Column("completed_at",sa.DateTime(timezone=True)),sa.Column("result",postgresql.JSONB()),
        sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.UniqueConstraint("action_plan_id",name="uq_agent_tasks_action_plan_id"))
    for col in ("workspace_id","action_plan_id","agent_id","status"):
        op.create_index(f"ix_agent_tasks_{col}","agent_tasks",[col])

def downgrade():
    op.drop_table("agent_tasks")
    op.drop_table("action_plans")
