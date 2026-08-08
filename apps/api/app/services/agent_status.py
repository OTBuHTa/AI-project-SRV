from datetime import UTC, datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.core import Agent, Resource

OFFLINE_AFTER_SECONDS = 90

def evaluate_agent_statuses(db: Session, workspace_id=None) -> tuple[int, int]:
    cutoff = datetime.now(UTC) - timedelta(seconds=OFFLINE_AFTER_SECONDS)
    query = select(Agent).where(Agent.revoked_at.is_(None))
    if workspace_id is not None:
        query = query.where(Agent.workspace_id == workspace_id)
    agents = db.scalars(query).all()
    changed = 0
    for agent in agents:
        expected = "offline" if not agent.last_seen_at or agent.last_seen_at < cutoff else (
            "online" if agent.status == "healthy" else "degraded"
        )
        resource = db.get(Resource, agent.resource_id)
        if resource and resource.status != expected:
            resource.status = expected
            changed += 1
    if changed:
        db.commit()
    return len(agents), changed
