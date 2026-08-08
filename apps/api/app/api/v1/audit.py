from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.session import get_db
from app.models.core import AuditLog

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("")
def list_audit(
    context=Depends(require_permission("audit.read")),
    db: Session = Depends(get_db),
    limit: int = 100,
):
    workspace, _ = context
    limit = min(max(limit, 1), 500)
    events = db.scalars(
        select(AuditLog)
        .where(AuditLog.workspace_id == workspace.id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    ).all()
    return [
        {
            "id": row.id,
            "action": row.action,
            "actor_id": row.actor_id,
            "result": row.result,
            "target_type": row.target_type,
            "target_id": row.target_id,
            "request_id": row.request_id,
            "hash": row.hash,
            "previous_hash": row.previous_hash,
            "created_at": row.created_at,
        }
        for row in events
    ]
