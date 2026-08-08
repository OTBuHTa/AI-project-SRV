import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.core import ActionPlan, Agent, Resource, User
from app.schemas.ai_actions import AIActionProposalRequest, AIActionProposalResponse
from app.services.audit import append_audit
from app.services.policy import get_capability_policy

router = APIRouter(prefix="/api/v1/ai", tags=["ai-actions"])
CONTAINER_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")


def _docker_inventory(resource: Resource, agent: Agent) -> dict:
    return ((resource.metadata_json or {}).get("docker") or (agent.last_metrics or {}).get("docker") or {})


def _select_container(payload: AIActionProposalRequest, inventory: dict) -> tuple[str, str]:
    containers = [c for c in inventory.get("containers", []) if c.get("name")]
    by_name = {str(c["name"]): c for c in containers}
    if payload.container:
        name = payload.container
        if not CONTAINER_RE.fullmatch(name):
            raise HTTPException(422, "invalid_container_name")
        if name not in by_name:
            raise HTTPException(409, "container_not_in_last_inventory")
        return name, str(by_name[name].get("state") or "unknown").lower()

    stopped = [c for c in containers if str(c.get("state") or "").lower() != "running"]
    if len(stopped) == 1:
        return str(stopped[0]["name"]), str(stopped[0].get("state") or "unknown").lower()
    raise HTTPException(422, "container_required_for_safe_proposal")


@router.post("/action-proposals", response_model=AIActionProposalResponse, status_code=201)
def create_ai_action_proposal(
    payload: AIActionProposalRequest,
    context=Depends(require_permission("action.create")),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace, _ = context
    resource = db.get(Resource, payload.resource_id)
    if not resource or resource.workspace_id != workspace.id:
        raise HTTPException(404, "resource_not_found")
    agent = db.scalar(select(Agent).where(Agent.resource_id == resource.id, Agent.revoked_at.is_(None)))
    if not agent:
        raise HTTPException(409, "agent_unavailable")
    capability = "docker.container.restart"
    if capability not in (agent.capabilities or []):
        raise HTTPException(409, "capability_not_supported_by_agent")

    inventory = _docker_inventory(resource, agent)
    if not inventory.get("available"):
        raise HTTPException(409, "docker_inventory_unavailable")
    container, state = _select_container(payload, inventory)

    # Capability selection is deterministic and policy-controlled. The LLM cannot invent executable tools.
    policy = get_capability_policy(capability)
    if not policy.allowed:
        raise HTTPException(403, "capability_blocked_by_policy")
    rationale = (
        f"AI Assistant proposes restarting Docker container '{container}'. "
        f"Last observed state: '{state}'. User intent: {payload.message.strip()[:800]}"
    )
    row = ActionPlan(
        workspace_id=workspace.id,
        user_id=user.id,
        resource_id=resource.id,
        capability=capability,
        parameters={"container": container},
        rationale=rationale,
        risk_level=policy.risk_level,
        requires_approval=policy.requires_approval,
        status="pending_approval",
        source="ai_proposal",
        verification_status="pending",
    )
    db.add(row)
    db.flush()
    append_audit(
        db,
        action="ai.action_proposal.create",
        actor_id=str(user.id),
        organization_id=workspace.organization_id,
        workspace_id=workspace.id,
        target_type="action_plan",
        target_id=str(row.id),
        details={
            "capability": capability,
            "container": container,
            "observed_state": state,
            "risk_level": policy.risk_level,
        },
    )
    db.commit()
    db.refresh(row)
    return AIActionProposalResponse(
        action_plan_id=row.id,
        resource_id=row.resource_id,
        capability=row.capability,
        parameters=row.parameters,
        rationale=row.rationale or "",
        risk_level=row.risk_level,
        requires_approval=row.requires_approval,
        status=row.status,
        source=row.source,
        created_at=row.created_at,
    )
