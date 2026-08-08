from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import BackupAlertEvent
from app.services.backup_alerts import BackupAlert


def sync_backup_alert_events(
    db: Session,
    *,
    workspace_id: str,
    alerts: list[BackupAlert],
    now: datetime | None = None,
) -> list[BackupAlertEvent]:
    now = now or datetime.now(timezone.utc)

    existing = list(
        db.scalars(
            select(BackupAlertEvent).where(
                BackupAlertEvent.workspace_id == workspace_id,
                BackupAlertEvent.active.is_(True),
            )
        ).all()
    )

    active_by_code = {event.code: event for event in existing}
    current_codes = {alert.code for alert in alerts}
    current_events: list[BackupAlertEvent] = []

    for alert in alerts:
        event = active_by_code.get(alert.code)

        if event is None:
            event = BackupAlertEvent(
                id=str(uuid4()),
                workspace_id=workspace_id,
                code=alert.code,
                severity=alert.severity,
                message=alert.message,
                active=True,
                first_seen_at=now,
                last_seen_at=now,
            )
            db.add(event)
        else:
            event.severity = alert.severity
            event.message = alert.message
            event.last_seen_at = now

        current_events.append(event)

    for event in existing:
        if event.code not in current_codes:
            event.active = False
            event.resolved_at = now
            event.last_seen_at = now

    db.commit()
    return current_events


def acknowledge_backup_alert(
    db: Session,
    *,
    workspace_id: str,
    event_id: str,
    acknowledged_by: str,
    now: datetime | None = None,
) -> BackupAlertEvent | None:
    now = now or datetime.now(timezone.utc)

    event = db.scalar(
        select(BackupAlertEvent).where(
            BackupAlertEvent.id == event_id,
            BackupAlertEvent.workspace_id == workspace_id,
        )
    )

    if event is None:
        return None

    event.acknowledged_at = now
    event.acknowledged_by = acknowledged_by

    db.commit()
    db.refresh(event)

    return event
