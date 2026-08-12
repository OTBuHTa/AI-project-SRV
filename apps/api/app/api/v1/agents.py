import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.core import Agent, EnrollmentToken, Resource, TelemetrySample, User, ActionPlan, AgentTask
from app.schemas.agents import (
    AgentEnrollRequest,
    AgentEnrollResponse,
    AgentTokenRotateResponse,
    AgentRevokeResponse,
    AgentHeartbeatRequest,
    AgentResponse,
    TelemetryPoint,
    EnrollmentTokenCreate,
    EnrollmentTokenResponse,
)
from app.services.audit import append_audit
from app.services.realtime import hub
from app.services.action_verification import verify_pending_actions
from app.services.resource_inventory import reconcile_inventory_snapshot

from app.schemas.actions import TaskOut, TaskResult
from app.schemas.inventory import InventoryItemOut, InventorySnapshotInput

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

AGENT_TOKEN_TTL = timedelta(days=90)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _new_token(prefix: str) -> tuple[str, str]:
    raw = f"{prefix}_{secrets.token_urlsafe(32)}"
    return raw, _hash_token(raw)


def _authenticate_agent(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> Agent:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="agent_authentication_required")
    token_hash = _hash_token(authorization.removeprefix("Bearer ").strip())
    agent = db.scalar(select(Agent).where(Agent.token_hash == token_hash))
    if not agent or agent.revoked_at is not None:
        raise HTTPException(status_code=401, detail="invalid_agent_token")
    if agent.token_expires_at <= datetime.now(UTC):
        raise HTTPException(status_code=401, detail="expired_agent_token")
    return agent


@router.post("/enrollment-token", response_model=EnrollmentTokenResponse, status_code=status.HTTP_201_CREATED)
def create_enrollment_token(
    payload: EnrollmentTokenCreate,
    request: Request,
    context=Depends(require_permission("agent.install")),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace, _ = context
    raw, token_hash = _new_token("enroll")
    expires_at = datetime.now(UTC) + timedelta(minutes=payload.ttl_minutes)
    db.add(
        EnrollmentToken(
            workspace_id=workspace.id,
            created_by_user_id=user.id,
            name=payload.name,
            agent_type=payload.agent_type,
            token_hash=token_hash,
            expires_at=expires_at,
        )
    )
    append_audit(
        db,
        action="agent.enrollment_token.create",
        actor_id=str(user.id),
        organization_id=workspace.organization_id,
        workspace_id=workspace.id,
        request_id=getattr(request.state, "request_id", None),
        target_type="agent",
        details={"agent_type": payload.agent_type, "name": payload.name},
    )
    db.commit()
    return EnrollmentTokenResponse(token=raw, expires_at=expires_at)


@router.post("/enroll", response_model=AgentEnrollResponse, status_code=status.HTTP_201_CREATED)
def enroll_agent(payload: AgentEnrollRequest, request: Request, db: Session = Depends(get_db)):
    token_hash = _hash_token(payload.enrollment_token)
    enrollment = db.scalar(
        select(EnrollmentToken)
        .where(EnrollmentToken.token_hash == token_hash)
        .with_for_update()
    )
    now = datetime.now(UTC)
    if not enrollment or enrollment.used_at is not None or enrollment.expires_at <= now:
        raise HTTPException(status_code=401, detail="invalid_or_expired_enrollment_token")

    resource = Resource(
        workspace_id=enrollment.workspace_id,
        type="host",
        name=payload.hostname,
        hostname=payload.hostname,
        operating_system=payload.os_name,
        status="online",
        metadata_json={"architecture": payload.architecture},
    )
    db.add(resource)
    db.flush()
    raw_agent_token, agent_token_hash = _new_token("agent")
    agent = Agent(
        workspace_id=enrollment.workspace_id,
        resource_id=resource.id,
        agent_type=enrollment.agent_type,
        version=payload.agent_version,
        status="online",
        token_hash=agent_token_hash,
        token_expires_at=now + AGENT_TOKEN_TTL,
        capabilities=sorted(set(payload.capabilities)),
        last_seen_at=now,
    )
    db.add(agent)
    enrollment.used_at = now
    db.flush()
    append_audit(
        db,
        action="agent.enroll",
        actor_id=str(agent.id),
        workspace_id=enrollment.workspace_id,
        request_id=getattr(request.state, "request_id", None),
        target_type="resource",
        target_id=str(resource.id),
        details={"hostname": payload.hostname, "agent_version": payload.agent_version},
    )
    db.commit()
    return AgentEnrollResponse(
        agent_id=agent.id,
        resource_id=resource.id,
        agent_token=raw_agent_token,
        agent_token_expires_at=agent.token_expires_at,
    )


@router.post(
    "/{agent_id}/token/rotate",
    response_model=AgentTokenRotateResponse,
)
def rotate_agent_token(
    agent_id: uuid.UUID,
    request: Request,
    context=Depends(require_permission("agent.update")),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace, _ = context

    agent = db.scalar(
        select(Agent)
        .where(
            Agent.id == agent_id,
            Agent.workspace_id == workspace.id,
        )
        .with_for_update()
    )

    if agent is None:
        raise HTTPException(
            status_code=404,
            detail="agent_not_found",
        )

    if agent.revoked_at is not None:
        raise HTTPException(
            status_code=409,
            detail="agent_revoked",
        )

    now = datetime.now(UTC)
    raw_token, token_hash = _new_token("agent")

    agent.token_hash = token_hash
    agent.token_expires_at = now + AGENT_TOKEN_TTL
    agent.token_rotated_at = now

    append_audit(
        db,
        action="agent.token.rotate",
        actor_id=str(user.id),
        organization_id=workspace.organization_id,
        workspace_id=workspace.id,
        request_id=getattr(request.state, "request_id", None),
        target_type="agent",
        target_id=str(agent.id),
        details={
            "token_expires_at": agent.token_expires_at.isoformat(),
        },
    )

    db.commit()

    return AgentTokenRotateResponse(
        agent_id=agent.id,
        agent_token=raw_token,
        agent_token_expires_at=agent.token_expires_at,
        token_rotated_at=agent.token_rotated_at,
    )


@router.post(
    "/{agent_id}/revoke",
    response_model=AgentRevokeResponse,
)
def revoke_agent(
    agent_id: uuid.UUID,
    request: Request,
    context=Depends(require_permission("agent.revoke")),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace, _ = context

    agent = db.scalar(
        select(Agent)
        .where(
            Agent.id == agent_id,
            Agent.workspace_id == workspace.id,
        )
        .with_for_update()
    )

    if agent is None:
        raise HTTPException(
            status_code=404,
            detail="agent_not_found",
        )

    if agent.revoked_at is None:
        now = datetime.now(UTC)

        agent.revoked_at = now
        agent.status = "revoked"

        resource = db.get(Resource, agent.resource_id)
        if resource is not None:
            resource.status = "offline"

        append_audit(
            db,
            action="agent.revoke",
            actor_id=str(user.id),
            organization_id=workspace.organization_id,
            workspace_id=workspace.id,
            request_id=getattr(request.state, "request_id", None),
            target_type="agent",
            target_id=str(agent.id),
            details={
                "resource_id": str(agent.resource_id),
            },
        )

        db.commit()

    return AgentRevokeResponse(
        agent_id=agent.id,
        revoked_at=agent.revoked_at,
    )


@router.post("/{agent_id}/heartbeat", status_code=status.HTTP_204_NO_CONTENT)
async def heartbeat(
    agent_id: uuid.UUID,
    payload: AgentHeartbeatRequest,
    authenticated_agent: Agent = Depends(_authenticate_agent),
    db: Session = Depends(get_db),
):
    if authenticated_agent.id != agent_id:
        raise HTTPException(status_code=403, detail="agent_identity_mismatch")
    now = datetime.now(UTC)
    authenticated_agent.status = payload.status
    authenticated_agent.version = payload.agent_version
    authenticated_agent.capabilities = sorted(set(payload.capabilities))
    authenticated_agent.last_metrics = {**payload.metrics.model_dump(), "docker": payload.docker.model_dump() if payload.docker else None}
    authenticated_agent.last_seen_at = now
    resource = db.get(Resource, authenticated_agent.resource_id)
    docker_data = payload.docker.model_dump() if payload.docker else None
    if resource:
        resource.status = "online" if payload.status == "healthy" else "degraded"
        meta = dict(resource.metadata_json or {})
        if docker_data is not None:
            meta["docker"] = docker_data
        resource.metadata_json = meta
    m = payload.metrics
    db.add(TelemetrySample(
        workspace_id=authenticated_agent.workspace_id, resource_id=authenticated_agent.resource_id,
        agent_id=authenticated_agent.id, cpu_percent=m.cpu_percent, memory_percent=m.memory_percent,
        disk_percent=m.disk_percent, disk_free_bytes=m.disk_free_bytes, uptime_seconds=m.uptime_seconds,
        load_1m=m.load_1m, docker=docker_data,
    ))
    verify_pending_actions(db, authenticated_agent.workspace_id, authenticated_agent.resource_id, docker_data)
    db.commit()
    await hub.broadcast(authenticated_agent.workspace_id, {
        "type":"resource.telemetry", "resource_id":str(authenticated_agent.resource_id),
        "agent_id":str(authenticated_agent.id), "status":resource.status if resource else payload.status,
        "metrics":payload.metrics.model_dump(), "docker":docker_data, "timestamp":now.isoformat(),
    })




@router.post(
    "/{agent_id}/inventory",
    response_model=list[InventoryItemOut],
)
def submit_inventory(
    agent_id: uuid.UUID,
    payload: InventorySnapshotInput,
    authenticated_agent: Agent = Depends(_authenticate_agent),
    db: Session = Depends(get_db),
):
    if authenticated_agent.id != agent_id:
        raise HTTPException(
            status_code=403,
            detail="agent_identity_mismatch",
        )

    try:
        return reconcile_inventory_snapshot(
            db,
            workspace_id=authenticated_agent.workspace_id,
            resource_id=authenticated_agent.resource_id,
            items=[
                item.model_dump()
                for item in payload.items
            ],
        )
    except ValueError as exc:
        if str(exc) == "resource_not_found":
            raise HTTPException(
                status_code=404,
                detail="resource_not_found",
            ) from exc
        raise


@router.get("", response_model=list[AgentResponse])
def list_agents(
    context=Depends(require_permission("agent.read")),
    db: Session = Depends(get_db),
):
    workspace, _ = context
    rows = db.execute(
        select(Agent, Resource)
        .join(Resource, Resource.id == Agent.resource_id)
        .where(Agent.workspace_id == workspace.id, Agent.revoked_at.is_(None))
        .order_by(Resource.name)
    ).all()
    return [
        AgentResponse(
            id=agent.id,
            resource_id=resource.id,
            hostname=resource.hostname or resource.name,
            agent_type=agent.agent_type,
            version=agent.version,
            status=agent.status,
            last_seen_at=agent.last_seen_at,
            capabilities=agent.capabilities or [],
            metrics=agent.last_metrics,
        )
        for agent, resource in rows
    ]


@router.get("/{agent_id}/telemetry", response_model=list[TelemetryPoint])
def telemetry_history(
    agent_id: uuid.UUID,
    limit: int = 120,
    context=Depends(require_permission("resource.read")),
    db: Session = Depends(get_db),
):
    workspace, _ = context
    limit = max(1, min(limit, 1000))
    agent = db.get(Agent, agent_id)
    if not agent or agent.workspace_id != workspace.id:
        raise HTTPException(status_code=404, detail="agent_not_found")
    rows = db.scalars(
        select(TelemetrySample).where(TelemetrySample.agent_id == agent_id)
        .order_by(TelemetrySample.created_at.desc()).limit(limit)
    ).all()
    return [TelemetryPoint(
        timestamp=r.created_at, cpu_percent=r.cpu_percent, memory_percent=r.memory_percent,
        disk_percent=r.disk_percent, disk_free_bytes=r.disk_free_bytes, uptime_seconds=r.uptime_seconds,
        load_1m=r.load_1m, docker=r.docker,
    ) for r in reversed(rows)]


@router.get("/{agent_id}/tasks/next", response_model=TaskOut | None)
def next_task(agent_id: uuid.UUID, authenticated_agent: Agent = Depends(_authenticate_agent), db: Session = Depends(get_db)):
    if authenticated_agent.id != agent_id:
        raise HTTPException(status_code=403, detail="agent_identity_mismatch")
    now = datetime.now(UTC)
    task = db.scalar(
        select(AgentTask).where(
            AgentTask.agent_id == agent_id,
            AgentTask.status == "queued",
        ).order_by(AgentTask.created_at).with_for_update(skip_locked=True)
    )
    if not task:
        return None
    task.status = "leased"
    task.started_at = now
    task.lease_expires_at = now + timedelta(seconds=60)
    plan = db.get(ActionPlan, task.action_plan_id)
    if plan:
        plan.status = "executing"
    db.commit()
    return TaskOut(task_id=task.id, capability=task.capability, parameters=task.parameters, lease_seconds=60)


@router.post("/{agent_id}/tasks/{task_id}/result")
def submit_task_result(agent_id: uuid.UUID, task_id: uuid.UUID, payload: TaskResult, authenticated_agent: Agent = Depends(_authenticate_agent), db: Session = Depends(get_db)):
    if authenticated_agent.id != agent_id:
        raise HTTPException(status_code=403, detail="agent_identity_mismatch")
    task = db.get(AgentTask, task_id)
    if not task or task.agent_id != agent_id:
        raise HTTPException(status_code=404, detail="task_not_found")
    if task.status not in {"leased", "executing"}:
        raise HTTPException(status_code=409, detail="task_not_active")
    now=datetime.now(UTC)
    result=payload.model_dump()
    task.status = "succeeded" if payload.status == "success" else "failed"
    task.result=result
    task.completed_at=now
    plan=db.get(ActionPlan, task.action_plan_id)
    if plan:
        plan.status = "verifying" if payload.status == "success" else "failed"
        plan.result=result
        plan.completed_at=now if payload.status != "success" else None
        if payload.status != "success":
            plan.verification_status = "execution_failed"
            plan.verification_result = {"reason": "agent_task_failed", "exit_code": payload.exit_code}
        if payload.status == "success":
            plan.verification_status = "awaiting_fresh_heartbeat"
            plan.verification_started_at = now
        append_audit(db, action="action_plan.execute", actor_type="agent", actor_id=str(agent_id), workspace_id=task.workspace_id, target_type="action_plan", target_id=str(plan.id), result="success" if payload.status == "success" else "failed", details={"capability":task.capability,"exit_code":payload.exit_code,"duration_ms":payload.duration_ms})
    db.commit()
    return {"status":"accepted"}
