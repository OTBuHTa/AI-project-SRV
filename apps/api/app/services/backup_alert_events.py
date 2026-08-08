from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
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

    current_codes = {alert.code for alert in alerts}

    for alert in alerts:
        statement = insert(BackupAlertEvent).values(
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
                BackupAlertEvent.workspace_id,
                BackupAlertEvent.code,
            ],
            index_where=BackupAlertEvent.active.is_(True),
            set_={
                "severity": statement.excluded.severity,
                "message": statement.excluded.message,
                "last_seen_at": statement.excluded.last_seen_at,
            },
        )

        db.execute(statement)

    existing = list(
        db.scalars(
            select(BackupAlertEvent).where(
                BackupAlertEvent.workspace_id == workspace_id,
                BackupAlertEvent.active.is_(True),
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
