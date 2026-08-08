from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class RetentionPolicy:
    keep_last: int = 7
    max_age_days: int = 30


def is_expired(
    created_at: datetime,
    *,
    now: datetime | None = None,
    max_age_days: int,
) -> bool:
    now = now or datetime.now(timezone.utc)

    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    return created_at < now - timedelta(days=max_age_days)


def select_artifacts_to_delete(
    artifacts: list,
    policy: RetentionPolicy,
    *,
    now: datetime | None = None,
) -> list:
    now = now or datetime.now(timezone.utc)

    ordered = sorted(
        artifacts,
        key=lambda item: item.created_at,
        reverse=True,
    )

    protected_ids = {
        item.id
        for item in ordered[: policy.keep_last]
    }

    return [
        item
        for item in ordered
        if item.id not in protected_ids
        and is_expired(
            item.created_at,
            now=now,
            max_age_days=policy.max_age_days,
        )
    ]
