import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import (
    Agent,
    AgentLifecycleAlertEvent,
)
from app.services.agent_lifecycle_alert_delivery_queue import (
    enqueue_agent_lifecycle_alert_delivery,
)
from app.services.agent_lifecycle_alert_events import (
    sync_agent_lifecycle_alert_events,
)
from app.services.agent_lifecycle_alerts import (
    evaluate_agent_lifecycle_alerts,
)
from app.services.agent_token_diagnostics import (
    get_agent_token_lifecycle_diagnostics,
)
from app.services.notification_routing import (
    find_matching_destinations,
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
    existing_active_codes = set(
        db.scalars(
            select(AgentLifecycleAlertEvent.code).where(
                AgentLifecycleAlertEvent.workspace_id
                == workspace_id,
                AgentLifecycleAlertEvent.active.is_(True),
            )
        ).all()
    )

    diagnostics = get_agent_token_lifecycle_diagnostics(
        db,
        workspace_id,
    )

    alerts = evaluate_agent_lifecycle_alerts(
        diagnostics
    )

    events = sync_agent_lifecycle_alert_events(
        db,
        workspace_id=workspace_id,
        alerts=alerts,
    )

    for event in events:
        if event.code in existing_active_codes:
            continue

        destinations = find_matching_destinations(
            db,
            event=event,
        )

        for destination in destinations:
            enqueue_agent_lifecycle_alert_delivery(
                db,
                workspace_id=workspace_id,
                alert_event_id=event.id,
                channel=destination.channel,
                destination_id=destination.id,
            )

    return events


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
