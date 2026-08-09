import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.services.backup_alert_delivery_transport import (
    DeliveryPayload,
    DeliveryTransportError,
    build_webhook_signature,
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


def test_build_webhook_signature():
    body = b'{"test":true}'

    result = build_webhook_signature(
        secret="secret",
        timestamp=1234567890,
        body=body,
    )

    expected = hmac.new(
        b"secret",
        b"1234567890." + body,
        hashlib.sha256,
    ).hexdigest()

    assert result == expected


@patch(
    "app.services.backup_alert_delivery_transport.time.time",
    return_value=1234567890,
)
@patch(
    "app.services.backup_alert_delivery_transport.httpx.post"
)
def test_deliver_webhook_signed(
    post,
    current_time,
):
    response = MagicMock()
    post.return_value = response

    deliver_webhook(
        url="https://example.invalid/hook",
        payload=payload(),
        timeout_seconds=5.0,
        signing_secret="test-secret",
    )

    post.assert_called_once()

    kwargs = post.call_args.kwargs

    assert kwargs["timeout"] == 5.0

    body = kwargs["content"]

    decoded = json.loads(body)

    assert decoded["delivery_id"] == "delivery-1"
    assert decoded["code"] == "backup_missing"

    assert kwargs["headers"]["X-AI-SRV-Timestamp"] == (
        "1234567890"
    )

    signature = build_webhook_signature(
        secret="test-secret",
        timestamp=1234567890,
        body=body,
    )

    assert kwargs["headers"]["X-AI-SRV-Signature"] == (
        f"sha256={signature}"
    )

    response.raise_for_status.assert_called_once()


@patch(
    "app.services.backup_alert_delivery_transport.httpx.post"
)
def test_deliver_webhook_without_secret_is_unsigned(post):
    response = MagicMock()
    post.return_value = response

    deliver_webhook(
        url="https://example.invalid/hook",
        payload=payload(),
    )

    headers = post.call_args.kwargs["headers"]

    assert "X-AI-SRV-Timestamp" not in headers
    assert "X-AI-SRV-Signature" not in headers


@patch(
    "app.services.backup_alert_delivery_transport.httpx.post"
)
def test_deliver_webhook_wraps_http_error(post):
    post.side_effect = httpx.ConnectError(
        "connection failed"
    )

    with pytest.raises(DeliveryTransportError):
        deliver_webhook(
            url="https://example.invalid/hook",
            payload=payload(),
        )
