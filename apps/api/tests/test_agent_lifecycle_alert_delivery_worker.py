from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.agent_lifecycle_alert_delivery_worker import (
    run_once,
)


def _settings():
    return SimpleNamespace(
        backup_alert_webhook_timeout_seconds=5.0,
        notification_webhook_allow_private_networks=False,
        notification_webhook_signing_secret=(
            "test-secret"
        ),
    )


def _delivery():
    return SimpleNamespace(
        id="delivery-1",
        workspace_id="workspace-1",
        alert_event_id="event-1",
        destination_id="destination-1",
    )


def _event():
    return SimpleNamespace(
        id="event-1",
        code="agent_token_rotation_expired",
        severity="warning",
        message="Expired agent token rotation",
    )


def _destination(
    *,
    enabled=True,
    channel="webhook",
    endpoint="https://example.invalid/hook",
):
    return SimpleNamespace(
        id="destination-1",
        workspace_id="workspace-1",
        channel=channel,
        enabled=enabled,
        endpoint=endpoint,
    )


@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "claim_due_agent_lifecycle_deliveries"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "get_settings"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "SessionLocal"
)
def test_worker_with_empty_queue(
    session_local,
    get_settings,
    claim_due,
):
    get_settings.return_value = _settings()

    db = MagicMock()
    session_local.return_value.__enter__.return_value = db
    claim_due.return_value = []

    assert run_once() == 0
    claim_due.assert_called_once()


@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "mark_agent_lifecycle_delivery_delivered"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "deliver_webhook"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "validate_notification_endpoint"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "claim_due_agent_lifecycle_deliveries"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "get_settings"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "SessionLocal"
)
def test_worker_delivers_lifecycle_alert(
    session_local,
    get_settings,
    claim_due,
    validate_endpoint,
    deliver,
    mark_delivered,
):
    get_settings.return_value = _settings()

    delivery = _delivery()
    event = _event()
    destination = _destination()

    db = MagicMock()
    session_local.return_value.__enter__.return_value = db
    claim_due.return_value = [delivery]
    db.scalar.side_effect = [
        event,
        destination,
    ]

    assert run_once() == 1

    validate_endpoint.assert_called_once_with(
        destination.endpoint,
        allow_private_networks=False,
    )

    deliver.assert_called_once()

    kwargs = deliver.call_args.kwargs

    assert kwargs["url"] == destination.endpoint
    assert kwargs["timeout_seconds"] == 5.0
    assert kwargs["signing_secret"] == "test-secret"

    payload = kwargs["payload"]

    assert payload.delivery_id == "delivery-1"
    assert payload.workspace_id == "workspace-1"
    assert payload.alert_event_id == "event-1"
    assert (
        payload.code
        == "agent_token_rotation_expired"
    )
    assert payload.severity == "warning"

    mark_delivered.assert_called_once_with(
        db,
        delivery=delivery,
    )


@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "mark_agent_lifecycle_delivery_failed"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "deliver_webhook"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "validate_notification_endpoint"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "claim_due_agent_lifecycle_deliveries"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "get_settings"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "SessionLocal"
)
def test_worker_marks_transport_failure(
    session_local,
    get_settings,
    claim_due,
    validate_endpoint,
    deliver,
    mark_failed,
):
    get_settings.return_value = _settings()

    delivery = _delivery()

    db = MagicMock()
    session_local.return_value.__enter__.return_value = db
    claim_due.return_value = [delivery]
    db.scalar.side_effect = [
        _event(),
        _destination(),
    ]

    error = RuntimeError("transport failed")
    deliver.side_effect = error

    assert run_once() == 1

    mark_failed.assert_called_once_with(
        db,
        delivery=delivery,
        error=error,
    )


@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "mark_agent_lifecycle_delivery_canceled"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "deliver_webhook"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "claim_due_agent_lifecycle_deliveries"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "get_settings"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "SessionLocal"
)
def test_worker_cancels_missing_destination(
    session_local,
    get_settings,
    claim_due,
    deliver,
    mark_canceled,
):
    get_settings.return_value = _settings()

    delivery = _delivery()

    db = MagicMock()
    session_local.return_value.__enter__.return_value = db
    claim_due.return_value = [delivery]
    db.scalar.side_effect = [
        _event(),
        None,
    ]

    assert run_once() == 1
    deliver.assert_not_called()

    mark_canceled.assert_called_once_with(
        db,
        delivery=delivery,
        reason="notification destination not found",
    )


@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "mark_agent_lifecycle_delivery_canceled"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "deliver_webhook"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "claim_due_agent_lifecycle_deliveries"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "get_settings"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "SessionLocal"
)
def test_worker_cancels_disabled_destination(
    session_local,
    get_settings,
    claim_due,
    deliver,
    mark_canceled,
):
    get_settings.return_value = _settings()

    delivery = _delivery()

    db = MagicMock()
    session_local.return_value.__enter__.return_value = db
    claim_due.return_value = [delivery]
    db.scalar.side_effect = [
        _event(),
        _destination(enabled=False),
    ]

    assert run_once() == 1
    deliver.assert_not_called()

    mark_canceled.assert_called_once_with(
        db,
        delivery=delivery,
        reason="notification destination disabled",
    )


@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "mark_agent_lifecycle_delivery_canceled"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "deliver_webhook"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "claim_due_agent_lifecycle_deliveries"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "get_settings"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "SessionLocal"
)
def test_worker_cancels_unsupported_channel(
    session_local,
    get_settings,
    claim_due,
    deliver,
    mark_canceled,
):
    get_settings.return_value = _settings()

    delivery = _delivery()

    db = MagicMock()
    session_local.return_value.__enter__.return_value = db
    claim_due.return_value = [delivery]
    db.scalar.side_effect = [
        _event(),
        _destination(channel="email"),
    ]

    assert run_once() == 1
    deliver.assert_not_called()

    mark_canceled.assert_called_once_with(
        db,
        delivery=delivery,
        reason=(
            "unsupported notification channel: email"
        ),
    )


@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "mark_agent_lifecycle_delivery_failed"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "deliver_webhook"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "claim_due_agent_lifecycle_deliveries"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "get_settings"
)
@patch(
    "app.services."
    "agent_lifecycle_alert_delivery_worker."
    "SessionLocal"
)
def test_worker_blocks_unsafe_endpoint(
    session_local,
    get_settings,
    claim_due,
    deliver,
    mark_failed,
):
    get_settings.return_value = _settings()

    delivery = _delivery()

    db = MagicMock()
    session_local.return_value.__enter__.return_value = db
    claim_due.return_value = [delivery]
    db.scalar.side_effect = [
        _event(),
        _destination(
            endpoint=(
                "http://169.254.169.254/"
                "latest/meta-data"
            )
        ),
    ]

    assert run_once() == 1

    deliver.assert_not_called()
    mark_failed.assert_called_once()

    kwargs = mark_failed.call_args.kwargs

    assert kwargs["delivery"] is delivery
    assert "link-local" in str(kwargs["error"])
