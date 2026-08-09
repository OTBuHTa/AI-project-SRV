from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.core import (
    BackupAlertEvent,
    BackupArtifact,
    BackupJob,
    BackupSchedule,
)
from app.services.backup_alert_events import sync_backup_alert_events
from app.services.backup_alert_delivery_queue import enqueue_alert_delivery
from app.services.notification_routing import find_matching_destinations
from app.services.backup_alerts import evaluate_backup_alerts
from app.services.backup_status import evaluate_backup_status


def _lock_workspace_backup_alerts(
    db: Session,
    *,
    workspace_id: str,
) -> None:
    db.execute(
        text(
            "SELECT pg_advisory_xact_lock("
            "hashtextextended(:workspace_id, 0)"
            ")"
        ),
        {"workspace_id": workspace_id},
    )


def sync_workspace_backup_alerts(
    db: Session,
    *,
    workspace_id: str,
) -> int:
    # Serialize the complete snapshot -> evaluate -> persist cycle
    # for a workspace. The transaction-scoped lock is released on commit.
    _lock_workspace_backup_alerts(
        db,
        workspace_id=workspace_id,
    )

    existing_active_codes = set(
        db.scalars(
            select(BackupAlertEvent.code).where(
                BackupAlertEvent.workspace_id == workspace_id,
                BackupAlertEvent.active.is_(True),
            )
        ).all()
    )

    artifacts = db.scalars(
        select(BackupArtifact)
        .join(
            BackupJob,
            BackupArtifact.backup_job_id == BackupJob.id,
        )
        .where(BackupJob.workspace_id == workspace_id)
        .order_by(BackupArtifact.created_at.desc())
    ).all()

    jobs = db.scalars(
        select(BackupJob)
        .where(BackupJob.workspace_id == workspace_id)
        .order_by(BackupJob.created_at.desc())
        .limit(100)
    ).all()

    schedule = db.scalar(
        select(BackupSchedule).where(
            BackupSchedule.workspace_id == workspace_id
        )
    )

    status = evaluate_backup_status(
        artifacts=artifacts,
        jobs=jobs,
        schedule=schedule,
    )

    alerts = evaluate_backup_alerts(status)

    events = sync_backup_alert_events(
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
            enqueue_alert_delivery(
                db,
                workspace_id=workspace_id,
                alert_event_id=event.id,
                channel=destination.channel,
                destination_id=destination.id,
            )

    return len(events)


def sync_scheduled_workspace_alerts(
    db: Session,
) -> int:
    workspace_ids = list(
        db.scalars(
            select(BackupSchedule.workspace_id)
            .where(BackupSchedule.enabled.is_(True))
        ).all()
    )

    synced = 0

    for workspace_id in workspace_ids:
        sync_workspace_backup_alerts(
            db,
            workspace_id=str(workspace_id),
        )
        synced += 1

    return synced
