import re
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.core import ActionPlan, Agent, AgentTask, Resource, User
from app.schemas.actions import ActionPlanCreate, ActionPlanOut
from app.services.audit import append_audit
from app.services.policy import get_capability_policy

router = APIRouter(prefix="/api/v1/action-plans", tags=["action-plans"])
CONTAINER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


def _out(row: ActionPlan) -> ActionPlanOut:
    return ActionPlanOut(id=row.id, resource_id=row.resource_id, capability=row.capability, parameters=row.parameters, rationale=row.rationale, risk_level=row.risk_level, requires_approval=row.requires_approval, status=row.status, approved_by_user_id=row.approved_by_user_id, approved_at=row.approved_at, completed_at=row.completed_at, result=row.result, source=row.source, verification_status=row.verification_status, verification_result=row.verification_result, verification_started_at=row.verification_started_at, verified_at=row.verified_at, created_at=row.created_at)


@router.post("", response_model=ActionPlanOut)
def create_action_plan(payload: ActionPlanCreate, context=Depends(require_permission("action.create")), user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    workspace, _ = context
    resource = db.get(Resource, payload.resource_id)
    if not resource or resource.workspace_id != workspace.id:
        raise HTTPException(404, "resource_not_found")
    agent = db.scalar(select(Agent).where(Agent.resource_id == resource.id, Agent.revoked_at.is_(None)))
    if not agent:
        raise HTTPException(409, "active_agent_required")
    policy = get_capability_policy(payload.capability)
    if not policy.allowed:
        raise HTTPException(403, "policy_blocked")
    if payload.capability not in (agent.capabilities or []):
        raise HTTPException(409, "capability_not_supported_by_agent")
    if payload.capability == "docker.container.restart":
        name = str(payload.parameters.get("container", ""))
        if not CONTAINER_RE.fullmatch(name):
            raise HTTPException(422, "invalid_container_name")
        docker = ((resource.metadata_json or {}).get("docker") or (agent.last_metrics or {}).get("docker") or {})
        known = {str(c.get("name")) for c in docker.get("containers", []) if c.get("name")}
        if name not in known:
            raise HTTPException(409, "container_not_in_last_inventory")
        parameters = {"container": name}
    else:
        parameters = payload.parameters
    row = ActionPlan(workspace_id=workspace.id, user_id=user.id, resource_id=resource.id, capability=payload.capability, parameters=parameters, rationale=payload.rationale, risk_level=policy.risk_level, requires_approval=policy.requires_approval, status="pending_approval")
    db.add(row); db.flush()
    append_audit(db, action="action_plan.create", actor_id=str(user.id), organization_id=workspace.organization_id, workspace_id=workspace.id, target_type="action_plan", target_id=str(row.id), details={"capability":row.capability,"risk_level":row.risk_level,"resource_id":str(resource.id)})
    db.commit(); db.refresh(row)
    return _out(row)


@router.get("", response_model=list[ActionPlanOut])
def list_action_plans(context=Depends(require_permission("action.read")), db: Session=Depends(get_db)):
    workspace, _ = context
    rows = db.scalars(select(ActionPlan).where(ActionPlan.workspace_id == workspace.id).order_by(ActionPlan.created_at.desc()).limit(200)).all()
    return [_out(r) for r in rows]


@router.post("/{plan_id}/approve", response_model=ActionPlanOut)
def approve_action_plan(plan_id: uuid.UUID, context=Depends(require_permission("action.approve")), user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    workspace, _ = context
    row = db.get(ActionPlan, plan_id)
    if not row or row.workspace_id != workspace.id:
        raise HTTPException(404, "action_plan_not_found")
    if row.status != "pending_approval":
        raise HTTPException(409, "action_plan_not_pending")
    agent = db.scalar(select(Agent).where(Agent.resource_id == row.resource_id, Agent.revoked_at.is_(None)))
    if not agent or row.capability not in (agent.capabilities or []):
        raise HTTPException(409, "capable_agent_unavailable")
    now=datetime.now(UTC)
    row.status="queued"; row.approved_by_user_id=user.id; row.approved_at=now
    task=AgentTask(workspace_id=workspace.id, action_plan_id=row.id, agent_id=agent.id, capability=row.capability, parameters=row.parameters, status="queued")
    db.add(task)
    append_audit(db, action="action_plan.approve", actor_id=str(user.id), organization_id=workspace.organization_id, workspace_id=workspace.id, target_type="action_plan", target_id=str(row.id), details={"capability":row.capability,"risk_level":row.risk_level})
    db.commit(); db.refresh(row)
    return _out(row)


@router.post("/{plan_id}/reject", response_model=ActionPlanOut)
def reject_action_plan(plan_id: uuid.UUID, context=Depends(require_permission("action.approve")), user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    workspace, _ = context
    row=db.get(ActionPlan, plan_id)
    if not row or row.workspace_id != workspace.id:
        raise HTTPException(404,"action_plan_not_found")
    if row.status != "pending_approval":
        raise HTTPException(409,"action_plan_not_pending")
    row.status="rejected"; row.completed_at=datetime.now(UTC)
    append_audit(db, action="action_plan.reject", actor_id=str(user.id), organization_id=workspace.organization_id, workspace_id=workspace.id, target_type="action_plan", target_id=str(row.id))
    db.commit(); db.refresh(row)
    return _out(row)
