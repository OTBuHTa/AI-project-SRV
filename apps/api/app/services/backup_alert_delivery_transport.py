from dataclasses import dataclass

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


def deliver_webhook(
    *,
    url: str,
    payload: DeliveryPayload,
    timeout_seconds: float = 10.0,
) -> None:
    try:
        response = httpx.post(
            url,
            json={
                "delivery_id": payload.delivery_id,
                "workspace_id": payload.workspace_id,
                "alert_event_id": payload.alert_event_id,
                "code": payload.code,
                "severity": payload.severity,
                "message": payload.message,
            },
            timeout=timeout_seconds,
        )
        response.raise_for_status()

    except httpx.HTTPError as exc:
        raise DeliveryTransportError(str(exc)) from exc
