from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.backup_alert_events import (
    acknowledge_backup_alert,
    sync_backup_alert_events,
)
from app.services.backup_alerts import BackupAlert


def test_sync_creates_active_alert():
    now = datetime(2026, 8, 9, tzinfo=timezone.utc)

    db = MagicMock()
    db.scalars.return_value.all.return_value = []

    events = sync_backup_alert_events(
        db,
        workspace_id="workspace-1",
        alerts=[
            BackupAlert(
                severity="critical",
                code="backup_missing",
                message="Backup missing",
            )
        ],
        now=now,
    )

    assert len(events) == 1
    assert events[0].workspace_id == "workspace-1"
    assert events[0].code == "backup_missing"
    assert events[0].active is True
    assert events[0].first_seen_at == now
    assert events[0].last_seen_at == now

    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_sync_updates_existing_active_alert():
    now = datetime(2026, 8, 9, tzinfo=timezone.utc)

    existing = SimpleNamespace(
        code="backup_missing",
        severity="warning",
        message="old",
        active=True,
        first_seen_at=now,
        last_seen_at=now,
        resolved_at=None,
    )

    db = MagicMock()
    db.scalars.return_value.all.return_value = [existing]

    events = sync_backup_alert_events(
        db,
        workspace_id="workspace-1",
        alerts=[
            BackupAlert(
                severity="critical",
                code="backup_missing",
                message="updated",
            )
        ],
        now=now,
    )

    assert events == [existing]
    assert existing.severity == "critical"
    assert existing.message == "updated"
    assert existing.last_seen_at == now

    db.add.assert_not_called()
    db.commit.assert_called_once()


def test_sync_resolves_disappeared_alert():
    now = datetime(2026, 8, 9, tzinfo=timezone.utc)

    existing = SimpleNamespace(
        code="recent_failures",
        active=True,
        last_seen_at=None,
        resolved_at=None,
    )

    db = MagicMock()
    db.scalars.return_value.all.return_value = [existing]

    events = sync_backup_alert_events(
        db,
        workspace_id="workspace-1",
        alerts=[],
        now=now,
    )

    assert events == []
    assert existing.active is False
    assert existing.resolved_at == now
    assert existing.last_seen_at == now


def test_acknowledge_backup_alert():
    now = datetime(2026, 8, 9, tzinfo=timezone.utc)

    event = SimpleNamespace(
        acknowledged_at=None,
        acknowledged_by=None,
    )

    db = MagicMock()
    db.scalar.return_value = event

    result = acknowledge_backup_alert(
        db,
        workspace_id="workspace-1",
        event_id="event-1",
        acknowledged_by="user-1",
        now=now,
    )

    assert result is event
    assert event.acknowledged_at == now
    assert event.acknowledged_by == "user-1"

    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(event)


def test_acknowledge_missing_alert_returns_none():
    db = MagicMock()
    db.scalar.return_value = None

    result = acknowledge_backup_alert(
        db,
        workspace_id="workspace-1",
        event_id="missing",
        acknowledged_by="user-1",
    )

    assert result is None
    db.commit.assert_not_called()
