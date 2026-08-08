from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class BackupHealth:
    status: str
    reason: str
    last_verified_at: datetime | None
    verified_count: int


def evaluate_backup_health(
    artifacts: list,
    *,
    max_verified_age_hours: int = 24,
    now: datetime | None = None,
) -> BackupHealth:
    now = now or datetime.now(timezone.utc)

    verified = [
        item
        for item in artifacts
        if getattr(item, "restore_verified", False)
    ]

    if not verified:
        return BackupHealth(
            status="failed",
            reason="no restore-verified backups",
            last_verified_at=None,
            verified_count=0,
        )

    latest = max(
        verified,
        key=lambda item: item.created_at,
    )

    created_at = latest.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    age_limit = now - timedelta(hours=max_verified_age_hours)

    if created_at < age_limit:
        return BackupHealth(
            status="degraded",
            reason="latest restore-verified backup is too old",
            last_verified_at=created_at,
            verified_count=len(verified),
        )

    return BackupHealth(
        status="healthy",
        reason="recent restore-verified backup available",
        last_verified_at=created_at,
        verified_count=len(verified),
    )
