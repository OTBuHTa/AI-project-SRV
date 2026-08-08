from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.services.backup_schedule_executor import (
    mark_schedule_started,
    mark_schedule_succeeded,
)


def test_mark_schedule_started_updates_times():
    now = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)

    schedule = SimpleNamespace(
        interval_minutes=60,
        last_run_at=None,
        next_run_at=None,
    )

    mark_schedule_started(
        schedule,
        now=now,
    )

    assert schedule.last_run_at == now
    assert schedule.next_run_at == now + timedelta(hours=1)


def test_mark_schedule_succeeded_updates_last_success():
    now = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)

    schedule = SimpleNamespace(
        last_success_at=None,
    )

    mark_schedule_succeeded(
        schedule,
        now=now,
    )

    assert schedule.last_success_at == now


def test_active_backup_statuses_match_backup_state_machine():
    from app.services.backup_schedule_executor import ACTIVE_BACKUP_STATUSES

    assert "created" in ACTIVE_BACKUP_STATUSES
    assert "running" in ACTIVE_BACKUP_STATUSES
    assert "restore_verified" not in ACTIVE_BACKUP_STATUSES
    assert "failed" not in ACTIVE_BACKUP_STATUSES
