from datetime import datetime, timezone

from app.services.backup_protection import (
    build_backup_protection_summary,
)
from app.services.backup_status import BackupStatus


def test_healthy_backup_is_protected():
    now = datetime.now(timezone.utc)

    status = BackupStatus(
        status="healthy",
        reason="backup protection is healthy",
        last_verified_at=now,
        verified_age_seconds=3600,
        failed_jobs=0,
        last_failure_at=None,
        scheduler_lag_seconds=0,
    )

    result = build_backup_protection_summary(status)

    assert result["protected"] is True
    assert result["status"] == "healthy"
    assert result["alerts"] == []


def test_degraded_backup_is_not_fully_protected():
    now = datetime.now(timezone.utc)

    status = BackupStatus(
        status="degraded",
        reason="recent backup failures detected",
        last_verified_at=now,
        verified_age_seconds=3600,
        failed_jobs=1,
        last_failure_at=now,
        scheduler_lag_seconds=0,
    )

    result = build_backup_protection_summary(status)

    assert result["protected"] is False
    assert result["status"] == "degraded"
    assert len(result["alerts"]) == 1


def test_missing_backup_is_not_protected():
    status = BackupStatus(
        status="failed",
        reason="no restore-verified backup available",
        last_verified_at=None,
        verified_age_seconds=None,
        failed_jobs=0,
        last_failure_at=None,
        scheduler_lag_seconds=0,
    )

    result = build_backup_protection_summary(status)

    assert result["protected"] is False
    assert result["status"] == "failed"
