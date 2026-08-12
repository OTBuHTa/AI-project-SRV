from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import Agent
from app.services.audit import append_audit


AGENT_TOKEN_ROTATION_PREPARE_TTL = timedelta(minutes=15)


def cleanup_expired_pending_rotations(
    db: Session,
    *,
    now: datetime | None = None,
) -> int:
    current_time = now or datetime.now(UTC)
    cutoff = current_time - AGENT_TOKEN_ROTATION_PREPARE_TTL

    agents = db.scalars(
        select(Agent)
        .where(
            Agent.pending_token_hash.is_not(None),
            Agent.token_rotation_prepared_at.is_not(None),
            Agent.token_rotation_prepared_at <= cutoff,
        )
        .with_for_update()
    ).all()

    if not agents:
        return 0

    for agent in agents:
        prepared_at = agent.token_rotation_prepared_at

        agent.pending_token_hash = None
        agent.pending_token_expires_at = None
        agent.token_rotation_prepared_at = None

        append_audit(
            db,
            action="agent.token.rotate.prepare.cleanup",
            actor_id=str(agent.id),
            workspace_id=agent.workspace_id,
            target_type="agent",
            target_id=str(agent.id),
            details={
                "token_rotation_prepared_at": (
                    prepared_at.isoformat()
                    if prepared_at is not None
                    else None
                ),
                "cleaned_at": current_time.isoformat(),
                "reason": "prepare_window_expired",
            },
        )

    db.commit()

    return len(agents)
