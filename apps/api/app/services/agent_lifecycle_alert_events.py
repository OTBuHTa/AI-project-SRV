from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.core import AgentLifecycleAlertEvent
from app.services.agent_lifecycle_alerts import AgentLifecycleAlert


def sync_agent_lifecycle_alert_events(
    db: Session,
    *,
    workspace_id: str,
    alerts: list[AgentLifecycleAlert],
    now: datetime | None = None,
) -> list[AgentLifecycleAlertEvent]:
    now = now or datetime.now(timezone.utc)

    current_codes = {alert.code for alert in alerts}

    for alert in alerts:
        statement = insert(
            AgentLifecycleAlertEvent
        ).values(
            workspace_id=workspace_id,
            code=alert.code,
            severity=alert.severity,
            message=alert.message,
            active=True,
            first_seen_at=now,
            last_seen_at=now,
        )

        statement = statement.on_conflict_do_update(
            index_elements=[
                AgentLifecycleAlertEvent.workspace_id,
                AgentLifecycleAlertEvent.code,
            ],
            index_where=(
                AgentLifecycleAlertEvent.active.is_(True)
            ),
            set_={
                "severity": statement.excluded.severity,
                "message": statement.excluded.message,
                "last_seen_at": statement.excluded.last_seen_at,
            },
        )

        db.execute(statement)

    existing = list(
        db.scalars(
            select(AgentLifecycleAlertEvent).where(
                AgentLifecycleAlertEvent.workspace_id
                == workspace_id,
                AgentLifecycleAlertEvent.active.is_(True),
            )
        ).all()
    )

    for event in existing:
        if event.code not in current_codes:
            event.active = False
            event.resolved_at = now
            event.last_seen_at = now

    db.commit()

    return [
        event
        for event in existing
        if event.code in current_codes
    ]
