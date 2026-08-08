from datetime import datetime, timedelta, timezone


MIN_INTERVAL_MINUTES = 15


def calculate_next_run(
    *,
    interval_minutes: int,
    from_time: datetime | None = None,
) -> datetime:
    if interval_minutes < MIN_INTERVAL_MINUTES:
        raise ValueError(
            f"backup interval must be at least {MIN_INTERVAL_MINUTES} minutes"
        )

    from_time = from_time or datetime.now(timezone.utc)

    if from_time.tzinfo is None:
        from_time = from_time.replace(tzinfo=timezone.utc)

    return from_time + timedelta(minutes=interval_minutes)


def schedule_is_due(
    next_run_at: datetime | None,
    *,
    now: datetime | None = None,
) -> bool:
    if next_run_at is None:
        return True

    now = now or datetime.now(timezone.utc)

    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    if next_run_at.tzinfo is None:
        next_run_at = next_run_at.replace(tzinfo=timezone.utc)

    return next_run_at <= now
