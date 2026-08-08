from datetime import datetime, timezone

from app.services.backup_alerts import evaluate_backup_alerts
from app.services.backup_status import BackupStatus


def status(
    *,
    state="healthy",
    last_verified_at=None,
    verified_age_seconds=0,
    failed_jobs=0,
    scheduler_lag_seconds=0,
):
    return BackupStatus(
        status=state,
        reason="test",
        last_verified_at=last_verified_at,
        verified_age_seconds=verified_age_seconds,
        failed_jobs=failed_jobs,
        last_failure_at=None,
        scheduler_lag_seconds=scheduler_lag_seconds,
    )


def test_no_alerts_when_backup_is_healthy():
    now = datetime.now(timezone.utc)

    alerts = evaluate_backup_alerts(
        status(
            last_verified_at=now,
            verified_age_seconds=3600,
        )
    )

    assert alerts == []


def test_missing_backup_is_critical():
    alerts = evaluate_backup_alerts(
        status(
            state="failed",
            last_verified_at=None,
            verified_age_seconds=None,
        )
    )

    assert len(alerts) == 1
    assert alerts[0].severity == "critical"
    assert alerts[0].code == "backup_missing"


def test_stale_backup_creates_warning():
    now = datetime.now(timezone.utc)

    alerts = evaluate_backup_alerts(
        status(
            state="degraded",
            last_verified_at=now,
            verified_age_seconds=25 * 3600,
        )
    )

    assert any(
        alert.code == "backup_stale"
        for alert in alerts
    )


def test_scheduler_lag_creates_warning():
    now = datetime.now(timezone.utc)

    alerts = evaluate_backup_alerts(
        status(
            state="degraded",
            last_verified_at=now,
            scheduler_lag_seconds=1800,
        )
    )

    assert any(
        alert.code == "scheduler_lag"
        for alert in alerts
    )


def test_recent_failures_create_warning():
    now = datetime.now(timezone.utc)

    alerts = evaluate_backup_alerts(
        status(
            state="degraded",
            last_verified_at=now,
            failed_jobs=2,
        )
    )

    assert any(
        alert.code == "recent_failures"
        for alert in alerts
    )
