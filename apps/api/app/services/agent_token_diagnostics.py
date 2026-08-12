from datetime import UTC, datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.core import Agent
from app.services.agent_token_lifecycle import (
    AGENT_TOKEN_ROTATION_PREPARE_TTL,
)


def get_agent_token_lifecycle_diagnostics(
    db: Session,
    workspace_id,
    *,
    now: datetime | None = None,
) -> dict:
    current_time = now or datetime.now(UTC)
    cutoff = current_time - AGENT_TOKEN_ROTATION_PREPARE_TTL

    pending_any = or_(
        Agent.pending_token_hash.is_not(None),
        Agent.pending_token_expires_at.is_not(None),
        Agent.token_rotation_prepared_at.is_not(None),
    )
    pending_complete = and_(
        Agent.pending_token_hash.is_not(None),
        Agent.pending_token_expires_at.is_not(None),
        Agent.token_rotation_prepared_at.is_not(None),
    )

    row = db.execute(
        select(
            func.count(Agent.id).label("agents_total"),
            func.count(Agent.id)
            .filter(
                Agent.pending_token_hash.is_not(None),
            )
            .label("pending_rotations"),
            func.count(Agent.id)
            .filter(
                Agent.pending_token_hash.is_not(None),
                Agent.token_rotation_prepared_at.is_not(None),
                Agent.token_rotation_prepared_at <= cutoff,
            )
            .label("expired_pending_rotations"),
            func.count(Agent.id)
            .filter(
                pending_any,
                ~pending_complete,
            )
            .label("incomplete_pending_rotations"),
            func.count(Agent.id)
            .filter(
                Agent.revoked_at.is_not(None),
                Agent.pending_token_hash.is_not(None),
            )
            .label("revoked_with_pending_rotation"),
            func.min(Agent.token_rotation_prepared_at)
            .filter(
                Agent.pending_token_hash.is_not(None),
            )
            .label("oldest_pending_prepared_at"),
        ).where(
            Agent.workspace_id == workspace_id,
        )
    ).one()

    oldest_pending = row.oldest_pending_prepared_at

    return {
        "workspace_id": str(workspace_id),
        "agents_total": row.agents_total,
        "pending_rotations": row.pending_rotations,
        "expired_pending_rotations": row.expired_pending_rotations,
        "incomplete_pending_rotations": row.incomplete_pending_rotations,
        "revoked_with_pending_rotation": row.revoked_with_pending_rotation,
        "oldest_pending_prepared_at": (
            oldest_pending.isoformat()
            if oldest_pending is not None
            else None
        ),
        "prepare_ttl_seconds": int(
            AGENT_TOKEN_ROTATION_PREPARE_TTL.total_seconds()
        ),
        "observed_at": current_time.isoformat(),
    }
