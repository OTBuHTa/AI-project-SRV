from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.services.backup_alert_delivery_transport import (
    DeliveryPayload,
    DeliveryTransportError,
    deliver_webhook,
)


def payload():
    return DeliveryPayload(
        delivery_id="delivery-1",
        workspace_id="workspace-1",
        alert_event_id="event-1",
        code="backup_missing",
        severity="critical",
        message="Backup missing",
    )


@patch("app.services.backup_alert_delivery_transport.httpx.post")
def test_deliver_webhook(post):
    response = MagicMock()
    post.return_value = response

    deliver_webhook(
        url="https://example.invalid/hook",
        payload=payload(),
        timeout_seconds=5.0,
    )

    post.assert_called_once()

    kwargs = post.call_args.kwargs

    assert kwargs["timeout"] == 5.0
    assert kwargs["json"]["delivery_id"] == "delivery-1"
    assert kwargs["json"]["code"] == "backup_missing"

    response.raise_for_status.assert_called_once()


@patch("app.services.backup_alert_delivery_transport.httpx.post")
def test_deliver_webhook_wraps_http_error(post):
    post.side_effect = httpx.ConnectError("connection failed")

    with pytest.raises(DeliveryTransportError):
        deliver_webhook(
            url="https://example.invalid/hook",
            payload=payload(),
        )
