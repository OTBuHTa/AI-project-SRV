import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import Agent, AgentLifecycleAlertEvent
from app.services.agent_lifecycle_alert_events import (
    sync_agent_lifecycle_alert_events,
)
from app.services.agent_lifecycle_alerts import (
    evaluate_agent_lifecycle_alerts,
)
from app.services.agent_token_diagnostics import (
    get_agent_token_lifecycle_diagnostics,
)


logger = logging.getLogger(__name__)


def _get_lifecycle_workspace_ids(
    db: Session,
) -> list[str]:
    agent_workspace_ids = db.scalars(
        select(Agent.workspace_id).distinct()
    ).all()

    active_alert_workspace_ids = db.scalars(
        select(AgentLifecycleAlertEvent.workspace_id)
        .where(
            AgentLifecycleAlertEvent.active.is_(True)
        )
        .distinct()
    ).all()

    return sorted(
        {
            str(workspace_id)
            for workspace_id in (
                list(agent_workspace_ids)
                + list(active_alert_workspace_ids)
            )
            if workspace_id is not None
        }
    )


def sync_workspace_agent_lifecycle_alerts(
    db: Session,
    *,
    workspace_id: str,
):
    diagnostics = get_agent_token_lifecycle_diagnostics(
        db,
        workspace_id,
    )

    alerts = evaluate_agent_lifecycle_alerts(
        diagnostics
    )

    return sync_agent_lifecycle_alert_events(
        db,
        workspace_id=workspace_id,
        alerts=alerts,
    )


def sync_all_agent_lifecycle_alerts(
    db: Session,
) -> int:
    workspace_ids = _get_lifecycle_workspace_ids(db)

    synced = 0

    for workspace_id in workspace_ids:
        try:
            sync_workspace_agent_lifecycle_alerts(
                db,
                workspace_id=workspace_id,
            )
        except Exception:
            db.rollback()
            logger.exception(
                "agent lifecycle alert reconciliation failed",
                extra={"workspace_id": workspace_id},
            )
            continue

        synced += 1

    return synced
