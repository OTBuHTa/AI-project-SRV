from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import BackupJob, BackupSchedule
from app.services.backup_scheduler import calculate_next_run


ACTIVE_BACKUP_STATUSES = {
    "created",
    "running",
}


def has_active_backup(
    db: Session,
    *,
    workspace_id: str,
) -> bool:
    job = db.scalar(
        select(BackupJob)
        .where(
            BackupJob.workspace_id == workspace_id,
            BackupJob.status.in_(ACTIVE_BACKUP_STATUSES),
        )
        .limit(1)
    )

    return job is not None


def mark_schedule_started(
    schedule: BackupSchedule,
    *,
    now: datetime | None = None,
) -> None:
    now = now or datetime.now(timezone.utc)

    schedule.last_run_at = now
    schedule.next_run_at = calculate_next_run(
        interval_minutes=schedule.interval_minutes,
        from_time=now,
    )


def mark_schedule_succeeded(
    schedule: BackupSchedule,
    *,
    now: datetime | None = None,
) -> None:
    now = now or datetime.now(timezone.utc)
    schedule.last_success_at = now


def get_due_schedules(
    db: Session,
    *,
    now: datetime | None = None,
    limit: int = 10,
) -> list[BackupSchedule]:
    now = now or datetime.now(timezone.utc)

    statement = (
        select(BackupSchedule)
        .where(
            BackupSchedule.enabled.is_(True),
            BackupSchedule.next_run_at.is_not(None),
            BackupSchedule.next_run_at <= now,
        )
        .order_by(BackupSchedule.next_run_at.asc())
        .limit(limit)
        .with_for_update(skip_locked=True)
    )

    return list(
        db.scalars(statement).all()
    )
