from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.backup_alert_delivery_worker import run_once


@patch("app.services.backup_alert_delivery_worker.claim_due_deliveries")
@patch("app.services.backup_alert_delivery_worker.get_settings")
@patch("app.services.backup_alert_delivery_worker.SessionLocal")
def test_worker_with_empty_queue(
    session_local,
    get_settings,
    claim_due,
):
    get_settings.return_value = SimpleNamespace(
        backup_alert_webhook_timeout_seconds=10.0,
        notification_webhook_allow_private_networks=False,
        notification_webhook_signing_secret="test-secret",
    )

    db = MagicMock()
    session_local.return_value.__enter__.return_value = db
    claim_due.return_value = []

    assert run_once() == 0

    claim_due.assert_called_once()


@patch("app.services.backup_alert_delivery_worker.mark_delivery_delivered")
@patch("app.services.backup_alert_delivery_worker.deliver_webhook")
@patch("app.services.backup_alert_delivery_worker.validate_notification_endpoint")
@patch("app.services.backup_alert_delivery_worker.claim_due_deliveries")
@patch("app.services.backup_alert_delivery_worker.get_settings")
@patch("app.services.backup_alert_delivery_worker.SessionLocal")
def test_worker_delivers_to_destination(
    session_local,
    get_settings,
    claim_due,
    validate_endpoint,
    deliver,
    mark_delivered,
):
    get_settings.return_value = SimpleNamespace(
        backup_alert_webhook_timeout_seconds=5.0,
        notification_webhook_allow_private_networks=False,
        notification_webhook_signing_secret="test-secret",
    )

    delivery = SimpleNamespace(
        id="delivery-1",
        workspace_id="workspace-1",
        alert_event_id="event-1",
        destination_id="destination-1",
    )

    event = SimpleNamespace(
        id="event-1",
        code="backup_missing",
        severity="critical",
        message="Backup missing",
    )

    destination = SimpleNamespace(
        id="destination-1",
        channel="webhook",
        endpoint="https://example.invalid/hook",
    )

    db = MagicMock()
    session_local.return_value.__enter__.return_value = db
    claim_due.return_value = [delivery]

    db.scalar.side_effect = [
        event,
        destination,
    ]

    result = run_once()

    assert result == 1

    deliver.assert_called_once()

    kwargs = deliver.call_args.kwargs

    assert kwargs["url"] == destination.endpoint
    assert kwargs["timeout_seconds"] == 5.0
    assert kwargs["signing_secret"] == "test-secret"
    assert kwargs["payload"].delivery_id == "delivery-1"
    assert kwargs["payload"].alert_event_id == "event-1"

    mark_delivered.assert_called_once_with(
        db,
        delivery=delivery,
    )


@patch("app.services.backup_alert_delivery_worker.mark_delivery_failed")
@patch("app.services.backup_alert_delivery_worker.deliver_webhook")
@patch("app.services.backup_alert_delivery_worker.validate_notification_endpoint")
@patch("app.services.backup_alert_delivery_worker.claim_due_deliveries")
@patch("app.services.backup_alert_delivery_worker.get_settings")
@patch("app.services.backup_alert_delivery_worker.SessionLocal")
def test_worker_marks_transport_failure(
    session_local,
    get_settings,
    claim_due,
    validate_endpoint,
    deliver,
    mark_failed,
):
    get_settings.return_value = SimpleNamespace(
        backup_alert_webhook_timeout_seconds=5.0,
        notification_webhook_allow_private_networks=False,
        notification_webhook_signing_secret="test-secret",
    )

    delivery = SimpleNamespace(
        id="delivery-1",
        workspace_id="workspace-1",
        alert_event_id="event-1",
        destination_id="destination-1",
    )

    event = SimpleNamespace(
        id="event-1",
        code="backup_missing",
        severity="critical",
        message="Backup missing",
    )

    destination = SimpleNamespace(
        id="destination-1",
        channel="webhook",
        endpoint="https://example.invalid/hook",
    )

    db = MagicMock()
    session_local.return_value.__enter__.return_value = db
    claim_due.return_value = [delivery]

    db.scalar.side_effect = [
        event,
        destination,
    ]

    error = RuntimeError("transport failed")
    deliver.side_effect = error

    result = run_once()

    assert result == 1

    mark_failed.assert_called_once_with(
        db,
        delivery=delivery,
        error=error,
    )


@patch("app.services.backup_alert_delivery_worker.mark_delivery_failed")
@patch("app.services.backup_alert_delivery_worker.deliver_webhook")
@patch("app.services.backup_alert_delivery_worker.claim_due_deliveries")
@patch("app.services.backup_alert_delivery_worker.get_settings")
@patch("app.services.backup_alert_delivery_worker.SessionLocal")
def test_worker_fails_missing_destination(
    session_local,
    get_settings,
    claim_due,
    deliver,
    mark_failed,
):
    get_settings.return_value = SimpleNamespace(
        backup_alert_webhook_timeout_seconds=5.0,
        notification_webhook_allow_private_networks=False,
        notification_webhook_signing_secret="test-secret",
    )

    delivery = SimpleNamespace(
        id="delivery-1",
        workspace_id="workspace-1",
        alert_event_id="event-1",
        destination_id="destination-1",
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

    db.scalar.side_effect = [
        event,
        None,
    ]

    result = run_once()

    assert result == 1

    deliver.assert_not_called()

    mark_failed.assert_called_once_with(
        db,
        delivery=delivery,
        error="notification destination not found or disabled",
    )

def test_worker_rejects_unsupported_destination_channel(monkeypatch):
    from types import SimpleNamespace

    from app.services import backup_alert_delivery_worker as worker

    delivery = SimpleNamespace(
        id="delivery-unsupported",
        workspace_id="workspace-1",
        alert_event_id="event-1",
        destination_id="destination-1",
    )

    event = SimpleNamespace(
        id="event-1",
        workspace_id="workspace-1",
        code="backup_missing",
        severity="critical",
        message="test",
    )

    destination = SimpleNamespace(
        id="destination-1",
        workspace_id="workspace-1",
        channel="email",
        endpoint="test@example.invalid",
        enabled=True,
    )

    db = SimpleNamespace()

    class FakeSession:
        def __enter__(self):
            return db

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        worker,
        "SessionLocal",
        lambda: FakeSession(),
    )

    monkeypatch.setattr(
        worker,
        "claim_due_deliveries",
        lambda *_args, **_kwargs: [delivery],
    )

    def fake_scalar(_query):
        fake_scalar.calls += 1

        if fake_scalar.calls == 1:
            return event

        return destination

    fake_scalar.calls = 0
    db.scalar = fake_scalar

    failures = []

    monkeypatch.setattr(
        worker,
        "mark_delivery_failed",
        lambda *_args, **kwargs: failures.append(
            kwargs["error"]
        ),
    )

    def fail_if_webhook_called(**_kwargs):
        raise AssertionError(
            "webhook transport must not run"
        )

    monkeypatch.setattr(
        worker,
        "deliver_webhook",
        fail_if_webhook_called,
    )

    processed = worker.run_once()

    assert processed == 1
    assert failures == [
        "unsupported notification channel: email"
    ]


@patch(
    "app.services.backup_alert_delivery_worker."
    "mark_delivery_failed"
)
@patch(
    "app.services.backup_alert_delivery_worker."
    "deliver_webhook"
)
@patch(
    "app.services.backup_alert_delivery_worker."
    "claim_due_deliveries"
)
@patch(
    "app.services.backup_alert_delivery_worker."
    "get_settings"
)
@patch(
    "app.services.backup_alert_delivery_worker."
    "SessionLocal"
)
def test_worker_blocks_unsafe_destination_endpoint(
    session_local,
    get_settings,
    claim_due,
    deliver,
    mark_failed,
):
    get_settings.return_value = SimpleNamespace(
        backup_alert_webhook_timeout_seconds=5.0,
        notification_webhook_allow_private_networks=False,
        notification_webhook_signing_secret="test-secret",
    )

    delivery = SimpleNamespace(
        id="delivery-ssrf",
        workspace_id="workspace-1",
        alert_event_id="event-1",
        destination_id="destination-1",
    )

    event = SimpleNamespace(
        id="event-1",
        code="backup_missing",
        severity="critical",
        message="Backup missing",
    )

    destination = SimpleNamespace(
        id="destination-1",
        channel="webhook",
        endpoint="http://169.254.169.254/latest/meta-data",
    )

    db = MagicMock()
    session_local.return_value.__enter__.return_value = db
    claim_due.return_value = [delivery]

    db.scalar.side_effect = [
        event,
        destination,
    ]

    result = run_once()

    assert result == 1

    deliver.assert_not_called()

    mark_failed.assert_called_once()

    kwargs = mark_failed.call_args.kwargs

    assert kwargs["delivery"] is delivery
    assert "link-local" in str(kwargs["error"])
