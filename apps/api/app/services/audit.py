import hashlib
import json
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import AuditLog


def _digest(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def append_audit(
    db: Session,
    *,
    action: str,
    actor_id: str | None = None,
    organization_id: uuid.UUID | None = None,
    workspace_id: uuid.UUID | None = None,
    request_id: str | None = None,
    source_ip: str | None = None,
    result: str = "success",
    target_type: str | None = None,
    target_id: str | None = None,
    details: dict | None = None,
) -> AuditLog:
    previous = db.scalar(select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(1))
    previous_hash = previous.hash if previous else None
    created_at = datetime.now(UTC)
    event = {
        "organization_id": organization_id,
        "workspace_id": workspace_id,
        "actor_id": actor_id,
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "request_id": request_id,
        "source_ip": source_ip,
        "result": result,
        "details": details or {},
        "created_at": created_at.isoformat(),
        "previous_hash": previous_hash,
    }
    row = AuditLog(
        organization_id=organization_id,
        workspace_id=workspace_id,
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        request_id=request_id,
        source_ip=source_ip,
        result=result,
        details=details or {},
        previous_hash=previous_hash,
        hash=_digest(event),
        created_at=created_at,
    )
    db.add(row)
    return row
