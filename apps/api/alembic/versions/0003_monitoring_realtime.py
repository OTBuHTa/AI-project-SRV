"""monitoring telemetry and realtime
Revision ID: 0003_monitoring_realtime
Revises: 0002_agents_linux
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="0003_monitoring_realtime"
down_revision="0002_agents_linux"
branch_labels=None
depends_on=None

def upgrade():
    op.create_table("telemetry_samples",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cpu_percent", sa.Float(), nullable=False), sa.Column("memory_percent", sa.Float(), nullable=False),
        sa.Column("disk_percent", sa.Float(), nullable=False), sa.Column("disk_free_bytes", sa.BigInteger(), nullable=False),
        sa.Column("uptime_seconds", sa.BigInteger(), nullable=False), sa.Column("load_1m", sa.Float(), nullable=True),
        sa.Column("docker", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_telemetry_samples_workspace_id","telemetry_samples",["workspace_id"])
    op.create_index("ix_telemetry_samples_resource_id","telemetry_samples",["resource_id"])
    op.create_index("ix_telemetry_samples_agent_id","telemetry_samples",["agent_id"])
    op.create_index("ix_telemetry_samples_created_at","telemetry_samples",["created_at"])

def downgrade():
    op.drop_table("telemetry_samples")
