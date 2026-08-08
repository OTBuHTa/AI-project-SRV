from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import ActionPlan
from app.services.audit import append_audit


def _container_state(docker: dict | None, container_name: str) -> str | None:
    if not docker:
        return None
    for item in docker.get("containers", []):
        if str(item.get("name")) == container_name:
            return str(item.get("state") or "").lower() or None
    return None


def verify_pending_actions(db: Session, workspace_id, resource_id, docker: dict | None) -> list[ActionPlan]:
    """Verify completed agent tasks using fresh heartbeat inventory, never command stdout alone."""
    rows = db.scalars(
        select(ActionPlan).where(
            ActionPlan.workspace_id == workspace_id,
            ActionPlan.resource_id == resource_id,
            ActionPlan.status == "verifying",
        )
    ).all()
    changed: list[ActionPlan] = []
    now = datetime.now(UTC)
    for plan in rows:
        if plan.capability != "docker.container.restart":
            plan.status = "verification_failed"
            plan.verification_status = "unsupported_verifier"
            plan.verification_result = {"reason": "no_verifier_registered"}
        else:
            container = str((plan.parameters or {}).get("container", ""))
            state = _container_state(docker, container)
            if state == "running":
                plan.status = "succeeded"
                plan.verification_status = "verified"
                plan.verification_result = {"container": container, "observed_state": state}
            elif state is None:
                plan.status = "verification_failed"
                plan.verification_status = "not_observed"
                plan.verification_result = {"container": container, "observed_state": None}
            else:
                plan.status = "verification_failed"
                plan.verification_status = "unexpected_state"
                plan.verification_result = {"container": container, "observed_state": state}
        plan.verified_at = now
        plan.completed_at = now
        append_audit(
            db,
            action="action_plan.verify",
            actor_type="system",
            actor_id="verification-engine",
            workspace_id=workspace_id,
            target_type="action_plan",
            target_id=str(plan.id),
            result="success" if plan.verification_status == "verified" else "failed",
            details=plan.verification_result or {},
        )
        changed.append(plan)
    return changed
