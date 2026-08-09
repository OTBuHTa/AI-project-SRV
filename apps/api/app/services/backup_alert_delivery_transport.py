import hashlib
import hmac
import json
import time
from dataclasses import asdict, dataclass

import httpx


@dataclass(frozen=True)
class DeliveryPayload:
    delivery_id: str
    workspace_id: str
    alert_event_id: str
    code: str
    severity: str
    message: str


class DeliveryTransportError(RuntimeError):
    pass


def build_webhook_signature(
    *,
    secret: str,
    timestamp: int,
    body: bytes,
) -> str:
    signed = str(timestamp).encode() + b"." + body

    return hmac.new(
        secret.encode(),
        signed,
        hashlib.sha256,
    ).hexdigest()


def deliver_webhook(
    *,
    url: str,
    payload: DeliveryPayload,
    timeout_seconds: float = 10.0,
    signing_secret: str = "",
) -> None:
    body = json.dumps(
        asdict(payload),
        separators=(",", ":"),
        sort_keys=True,
    ).encode()

    headers = {
        "Content-Type": "application/json",
    }

    if signing_secret:
        timestamp = int(time.time())

        signature = build_webhook_signature(
            secret=signing_secret,
            timestamp=timestamp,
            body=body,
        )

        headers["X-AI-SRV-Timestamp"] = str(timestamp)
        headers["X-AI-SRV-Signature"] = (
            f"sha256={signature}"
        )

    try:
        response = httpx.post(
            url,
            content=body,
            headers=headers,
            timeout=timeout_seconds,
        )
        response.raise_for_status()

    except httpx.HTTPError as exc:
        raise DeliveryTransportError(str(exc)) from exc
