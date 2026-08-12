import uuid
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import require_permission
from app.core.security import decode_access_token
from app.db.session import SessionLocal, get_db
from app.models.core import Membership
from app.services.realtime import hub
from app.services.agent_status import OFFLINE_AFTER_SECONDS, evaluate_agent_statuses
from app.services.agent_token_diagnostics import get_agent_token_lifecycle_diagnostics

router=APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])

@router.post("/evaluate-status")
def evaluate_status(context=Depends(require_permission("agent.read")), db: Session=Depends(get_db)):
    workspace,_=context
    evaluated, changed = evaluate_agent_statuses(db, workspace.id)
    return {"evaluated":evaluated,"changed":changed,"offline_after_seconds":OFFLINE_AFTER_SECONDS}

@router.get("/agent-token-lifecycle")
def agent_token_lifecycle_diagnostics(
    context=Depends(require_permission("agent.read")),
    db: Session=Depends(get_db),
):
    workspace, _ = context
    return get_agent_token_lifecycle_diagnostics(
        db,
        workspace.id,
    )


@router.websocket("/ws/{workspace_id}")
async def workspace_ws(websocket: WebSocket, workspace_id: uuid.UUID, token: str):
    try:
        claims=decode_access_token(token)
        user_id=uuid.UUID(claims["sub"])
    except Exception:
        await websocket.close(code=4401); return
    with SessionLocal() as db:
        membership=db.scalar(select(Membership).where(Membership.user_id==user_id, Membership.workspace_id==workspace_id))
        if not membership:
            await websocket.close(code=4403); return
    await hub.connect(workspace_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await hub.disconnect(workspace_id, websocket)
