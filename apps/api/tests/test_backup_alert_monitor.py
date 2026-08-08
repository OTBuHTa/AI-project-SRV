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


@patch("app.services.backup_alert_monitor.sync_backup_alert_events")
@patch("app.services.backup_alert_monitor.evaluate_backup_alerts")
@patch("app.services.backup_alert_monitor.evaluate_backup_status")
@patch("app.services.backup_alert_monitor._lock_workspace_backup_alerts")
def test_sync_workspace_backup_alerts(
    lock_workspace,
    evaluate_status,
    evaluate_alerts,
    sync_events,
):
    db = MagicMock()

    db.scalars.return_value.all.return_value = []
    db.scalar.return_value = None

    status = MagicMock()
    alerts = [MagicMock(), MagicMock()]

    evaluate_status.return_value = status
    evaluate_alerts.return_value = alerts
    sync_events.return_value = [MagicMock(), MagicMock()]

    result = sync_workspace_backup_alerts(
        db,
        workspace_id="workspace-1",
    )

    assert result == 2

    lock_workspace.assert_called_once_with(
        db,
        workspace_id="workspace-1",
    )

    sync_events.assert_called_once_with(
        db,
        workspace_id="workspace-1",
        alerts=alerts,
    )


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
