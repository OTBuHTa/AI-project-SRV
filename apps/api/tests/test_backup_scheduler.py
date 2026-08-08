from datetime import datetime, timedelta, timezone

import pytest

from app.services.backup_scheduler import (
    calculate_next_run,
    schedule_is_due,
)


def test_calculate_next_run():
    now = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)

    result = calculate_next_run(
        interval_minutes=60,
        from_time=now,
    )

    assert result == now + timedelta(hours=1)


def test_rejects_too_short_interval():
    with pytest.raises(ValueError):
        calculate_next_run(interval_minutes=5)


def test_schedule_is_due():
    now = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)

    assert schedule_is_due(
        now - timedelta(minutes=1),
        now=now,
    )

    assert not schedule_is_due(
        now + timedelta(minutes=1),
        now=now,
    )


def test_schedule_without_next_run_is_due():
    assert schedule_is_due(None)
