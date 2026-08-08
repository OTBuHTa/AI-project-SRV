from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.backup_alert_delivery_worker import run_once


@patch("app.services.backup_alert_delivery_worker.get_settings")
@patch("app.services.backup_alert_delivery_worker.SessionLocal")
def test_worker_disabled_without_webhook(
    session_local,
    get_settings,
):
    get_settings.return_value = SimpleNamespace(
        backup_alert_webhook_url="",
        backup_alert_webhook_timeout_seconds=10.0,
    )

    assert run_once() == 0
    session_local.assert_not_called()


@patch("app.services.backup_alert_delivery_worker.mark_delivery_delivered")
@patch("app.services.backup_alert_delivery_worker.deliver_webhook")
@patch("app.services.backup_alert_delivery_worker.claim_due_deliveries")
@patch("app.services.backup_alert_delivery_worker.get_settings")
@patch("app.services.backup_alert_delivery_worker.SessionLocal")
def test_worker_delivers_webhook(
    session_local,
    get_settings,
    claim_due,
    deliver,
    mark_delivered,
):
    get_settings.return_value = SimpleNamespace(
        backup_alert_webhook_url="https://example.invalid/hook",
        backup_alert_webhook_timeout_seconds=5.0,
    )

    delivery = SimpleNamespace(
        id="delivery-1",
        workspace_id="workspace-1",
        alert_event_id="event-1",
    )

    event = SimpleNamespace(
        id="event-1",
        code="backup_missing",
        severity="critical",
        message="Backup missing",
    )

    db = MagicMock()
    session_local.return_value.__enter__.return_value = db
    claim_due.return_value = [delivery]
    db.scalar.return_value = event

    result = run_once()

    assert result == 1
    deliver.assert_called_once()
    mark_delivered.assert_called_once_with(
        db,
        delivery=delivery,
    )


@patch("app.services.backup_alert_delivery_worker.mark_delivery_failed")
@patch("app.services.backup_alert_delivery_worker.deliver_webhook")
@patch("app.services.backup_alert_delivery_worker.claim_due_deliveries")
@patch("app.services.backup_alert_delivery_worker.get_settings")
@patch("app.services.backup_alert_delivery_worker.SessionLocal")
def test_worker_marks_transport_failure(
    session_local,
    get_settings,
    claim_due,
    deliver,
    mark_failed,
):
    get_settings.return_value = SimpleNamespace(
        backup_alert_webhook_url="https://example.invalid/hook",
        backup_alert_webhook_timeout_seconds=5.0,
    )

    delivery = SimpleNamespace(
        id="delivery-1",
        workspace_id="workspace-1",
        alert_event_id="event-1",
    )

    event = SimpleNamespace(
        id="event-1",
        code="backup_missing",
        severity="critical",
        message="Backup missing",
    )

    db = MagicMock()
    session_local.return_value.__enter__.return_value = db
    claim_due.return_value = [delivery]
    db.scalar.return_value = event

    error = RuntimeError("transport failed")
    deliver.side_effect = error

    result = run_once()

    assert result == 1

    mark_failed.assert_called_once_with(
        db,
        delivery=delivery,
        error=error,
    )
