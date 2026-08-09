from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.backup_alert_monitor import (
    _lock_workspace_backup_alerts,
    sync_scheduled_workspace_alerts,
    sync_workspace_backup_alerts,
)


def test_workspace_alert_lock_uses_advisory_xact_lock():
    db = MagicMock()

    _lock_workspace_backup_alerts(
        db,
        workspace_id="workspace-1",
    )

    db.execute.assert_called_once()

    statement = str(db.execute.call_args.args[0])

    assert "pg_advisory_xact_lock" in statement
    assert "hashtextextended" in statement

    assert db.execute.call_args.args[1] == {
        "workspace_id": "workspace-1",
    }


@patch("app.services.backup_alert_monitor.enqueue_alert_delivery")
@patch("app.services.backup_alert_monitor.find_matching_destinations")
@patch("app.services.backup_alert_monitor.sync_backup_alert_events")
@patch("app.services.backup_alert_monitor.evaluate_backup_alerts")
@patch("app.services.backup_alert_monitor.evaluate_backup_status")
@patch("app.services.backup_alert_monitor._lock_workspace_backup_alerts")
def test_new_alert_enqueues_webhook_delivery(
    lock_workspace,
    evaluate_status,
    evaluate_alerts,
    sync_events,
    find_destinations,
    enqueue_delivery,
):
    db = MagicMock()

    # scalars() is called for:
    # 1. existing active alert codes
    # 2. backup artifacts
    # 3. backup jobs
    db.scalars.return_value.all.return_value = []
    db.scalar.return_value = None

    status = MagicMock()
    alerts = [MagicMock()]

    event = SimpleNamespace(
        id="event-1",
        workspace_id="workspace-1",
        code="backup_missing",
        severity="critical",
    )

    destination = SimpleNamespace(
        id="destination-1",
        channel="webhook",
    )

    evaluate_status.return_value = status
    evaluate_alerts.return_value = alerts
    sync_events.return_value = [event]
    find_destinations.return_value = [destination]

    result = sync_workspace_backup_alerts(
        db,
        workspace_id="workspace-1",
    )

    assert result == 1

    lock_workspace.assert_called_once_with(
        db,
        workspace_id="workspace-1",
    )

    sync_events.assert_called_once_with(
        db,
        workspace_id="workspace-1",
        alerts=alerts,
    )

    find_destinations.assert_called_once_with(
        db,
        event=event,
    )

    enqueue_delivery.assert_called_once_with(
        db,
        workspace_id="workspace-1",
        alert_event_id="event-1",
        channel="webhook",
        destination_id="destination-1",
    )


@patch("app.services.backup_alert_monitor.enqueue_alert_delivery")
@patch("app.services.backup_alert_monitor.sync_backup_alert_events")
@patch("app.services.backup_alert_monitor.evaluate_backup_alerts")
@patch("app.services.backup_alert_monitor.evaluate_backup_status")
@patch("app.services.backup_alert_monitor._lock_workspace_backup_alerts")
def test_existing_active_alert_does_not_enqueue_again(
    lock_workspace,
    evaluate_status,
    evaluate_alerts,
    sync_events,
    enqueue_delivery,
):
    db = MagicMock()

    existing_codes_result = MagicMock()
    existing_codes_result.all.return_value = [
        "backup_missing",
    ]

    empty_result = MagicMock()
    empty_result.all.return_value = []

    db.scalars.side_effect = [
        existing_codes_result,
        empty_result,
        empty_result,
    ]

    db.scalar.return_value = None

    status = MagicMock()
    alerts = [MagicMock()]

    event = SimpleNamespace(
        id="event-1",
        code="backup_missing",
    )

    evaluate_status.return_value = status
    evaluate_alerts.return_value = alerts
    sync_events.return_value = [event]

    result = sync_workspace_backup_alerts(
        db,
        workspace_id="workspace-1",
    )

    assert result == 1
    enqueue_delivery.assert_not_called()


@patch("app.services.backup_alert_monitor.sync_workspace_backup_alerts")
def test_sync_scheduled_workspace_alerts(sync_workspace):
    db = MagicMock()

    db.scalars.return_value.all.return_value = [
        "workspace-1",
        "workspace-2",
    ]

    result = sync_scheduled_workspace_alerts(db)

    assert result == 2
    assert sync_workspace.call_count == 2
