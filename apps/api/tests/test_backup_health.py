from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.services.backup_health import evaluate_backup_health


@dataclass
class Artifact:
    created_at: datetime
    restore_verified: bool


def test_backup_health_is_healthy_with_recent_verified_backup():
    now = datetime.now(timezone.utc)

    artifacts = [
        Artifact(
            created_at=now - timedelta(hours=2),
            restore_verified=True,
        )
    ]

    health = evaluate_backup_health(
        artifacts,
        now=now,
    )

    assert health.status == "healthy"


def test_backup_health_is_degraded_when_verified_backup_is_old():
    now = datetime.now(timezone.utc)

    artifacts = [
        Artifact(
            created_at=now - timedelta(days=2),
            restore_verified=True,
        )
    ]

    health = evaluate_backup_health(
        artifacts,
        now=now,
        max_verified_age_hours=24,
    )

    assert health.status == "degraded"


def test_backup_health_fails_without_verified_backup():
    health = evaluate_backup_health([])

    assert health.status == "failed"
