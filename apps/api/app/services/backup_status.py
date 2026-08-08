from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class BackupStatus:
    status: str
    reason: str
    last_verified_at: datetime | None
    verified_age_seconds: int | None
    failed_jobs: int
    last_failure_at: datetime | None
    scheduler_lag_seconds: int


def evaluate_backup_status(
    *,
    artifacts: list,
    jobs: list,
    schedule,
    now: datetime | None = None,
    max_verified_age_hours: int = 24,
    max_scheduler_lag_minutes: int = 10,
    failure_window_hours: int = 24,
) -> BackupStatus:
    now = now or datetime.now(timezone.utc)

    verified = [
        artifact
        for artifact in artifacts
        if getattr(artifact, "restore_verified", False)
    ]

    last_verified_at = None
    verified_age_seconds = None

    if verified:
        latest = max(
            verified,
            key=lambda artifact: artifact.created_at,
        )

        last_verified_at = latest.created_at

        if last_verified_at.tzinfo is None:
            last_verified_at = last_verified_at.replace(
                tzinfo=timezone.utc,
            )

        verified_age_seconds = max(
            0,
            int((now - last_verified_at).total_seconds()),
        )

    failure_cutoff = now - timedelta(hours=failure_window_hours)

    recent_failures = []

    for job in jobs:
        if getattr(job, "status", None) != "failed":
            continue

        created_at = getattr(job, "created_at", None)

        if created_at is None:
            continue

        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        if created_at >= failure_cutoff:
            recent_failures.append(created_at)

    failed_jobs = len(recent_failures)
    last_failure_at = max(recent_failures) if recent_failures else None

    scheduler_lag_seconds = 0

    if (
        schedule is not None
        and getattr(schedule, "enabled", False)
        and getattr(schedule, "next_run_at", None) is not None
    ):
        next_run_at = schedule.next_run_at

        if next_run_at.tzinfo is None:
            next_run_at = next_run_at.replace(
                tzinfo=timezone.utc,
            )

        scheduler_lag_seconds = max(
            0,
            int((now - next_run_at).total_seconds()),
        )

    if last_verified_at is None:
        return BackupStatus(
            status="failed",
            reason="no restore-verified backup available",
            last_verified_at=None,
            verified_age_seconds=None,
            failed_jobs=failed_jobs,
            last_failure_at=last_failure_at,
            scheduler_lag_seconds=scheduler_lag_seconds,
        )

    if verified_age_seconds > max_verified_age_hours * 3600:
        return BackupStatus(
            status="degraded",
            reason="latest restore-verified backup is too old",
            last_verified_at=last_verified_at,
            verified_age_seconds=verified_age_seconds,
            failed_jobs=failed_jobs,
            last_failure_at=last_failure_at,
            scheduler_lag_seconds=scheduler_lag_seconds,
        )

    if scheduler_lag_seconds > max_scheduler_lag_minutes * 60:
        return BackupStatus(
            status="degraded",
            reason="backup scheduler is behind schedule",
            last_verified_at=last_verified_at,
            verified_age_seconds=verified_age_seconds,
            failed_jobs=failed_jobs,
            last_failure_at=last_failure_at,
            scheduler_lag_seconds=scheduler_lag_seconds,
        )

    if failed_jobs > 0:
        return BackupStatus(
            status="degraded",
            reason="recent backup failures detected",
            last_verified_at=last_verified_at,
            verified_age_seconds=verified_age_seconds,
            failed_jobs=failed_jobs,
            last_failure_at=last_failure_at,
            scheduler_lag_seconds=scheduler_lag_seconds,
        )

    return BackupStatus(
        status="healthy",
        reason="backup protection is healthy",
        last_verified_at=last_verified_at,
        verified_age_seconds=verified_age_seconds,
        failed_jobs=0,
        last_failure_at=None,
        scheduler_lag_seconds=scheduler_lag_seconds,
    )
