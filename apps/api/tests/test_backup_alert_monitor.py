from unittest.mock import MagicMock, patch

from app.services.backup_alert_monitor import (
    sync_scheduled_workspace_alerts,
    sync_workspace_backup_alerts,
)


@patch("app.services.backup_alert_monitor.sync_backup_alert_events")
@patch("app.services.backup_alert_monitor.evaluate_backup_alerts")
@patch("app.services.backup_alert_monitor.evaluate_backup_status")
def test_sync_workspace_backup_alerts(
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
