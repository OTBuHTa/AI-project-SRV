from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.services.backup_status import evaluate_backup_status


def artifact(created_at, verified=True):
    return SimpleNamespace(
        created_at=created_at,
        restore_verified=verified,
    )


def job(status, created_at=None):
    return SimpleNamespace(
        status=status,
        created_at=created_at,
    )


def schedule(next_run_at=None, enabled=True):
    return SimpleNamespace(
        next_run_at=next_run_at,
        enabled=enabled,
    )


def test_backup_status_healthy():
    now = datetime(2026, 8, 9, 0, 0, tzinfo=timezone.utc)

    result = evaluate_backup_status(
        artifacts=[
            artifact(now - timedelta(hours=1)),
        ],
        jobs=[],
        schedule=schedule(
            now + timedelta(hours=1)
        ),
        now=now,
    )

    assert result.status == "healthy"
    assert result.failed_jobs == 0
    assert result.scheduler_lag_seconds == 0


def test_backup_status_failed_without_verified_backup():
    now = datetime(2026, 8, 9, 0, 0, tzinfo=timezone.utc)

    result = evaluate_backup_status(
        artifacts=[],
        jobs=[],
        schedule=None,
        now=now,
    )

    assert result.status == "failed"


def test_backup_status_degraded_when_verified_backup_is_old():
    now = datetime(2026, 8, 9, 0, 0, tzinfo=timezone.utc)

    result = evaluate_backup_status(
        artifacts=[
            artifact(now - timedelta(days=2)),
        ],
        jobs=[],
        schedule=None,
        now=now,
    )

    assert result.status == "degraded"


def test_backup_status_degraded_on_scheduler_lag():
    now = datetime(2026, 8, 9, 0, 0, tzinfo=timezone.utc)

    result = evaluate_backup_status(
        artifacts=[
            artifact(now - timedelta(hours=1)),
        ],
        jobs=[],
        schedule=schedule(
            now - timedelta(minutes=30)
        ),
        now=now,
    )

    assert result.status == "degraded"
    assert result.scheduler_lag_seconds == 1800


def test_backup_status_degraded_on_failed_jobs():
    now = datetime(2026, 8, 9, 0, 0, tzinfo=timezone.utc)

    result = evaluate_backup_status(
        artifacts=[
            artifact(now - timedelta(hours=1)),
        ],
        jobs=[
            job(
                "failed",
                created_at=now - timedelta(hours=2),
            )
        ],
        schedule=None,
        now=now,
    )

    assert result.status == "degraded"
    assert result.failed_jobs == 1


def test_old_failed_job_is_ignored():
    now = datetime(2026, 8, 9, 0, 0, tzinfo=timezone.utc)

    old_failure = SimpleNamespace(
        status="failed",
        created_at=now - timedelta(days=2),
    )

    result = evaluate_backup_status(
        artifacts=[
            artifact(now - timedelta(hours=1)),
        ],
        jobs=[old_failure],
        schedule=None,
        now=now,
    )

    assert result.status == "healthy"
    assert result.failed_jobs == 0
    assert result.last_failure_at is None


def test_recent_failure_sets_last_failure_at():
    now = datetime(2026, 8, 9, 0, 0, tzinfo=timezone.utc)
    failed_at = now - timedelta(hours=2)

    recent_failure = SimpleNamespace(
        status="failed",
        created_at=failed_at,
    )

    result = evaluate_backup_status(
        artifacts=[
            artifact(now - timedelta(hours=1)),
        ],
        jobs=[recent_failure],
        schedule=None,
        now=now,
    )

    assert result.status == "degraded"
    assert result.failed_jobs == 1
    assert result.last_failure_at == failed_at
