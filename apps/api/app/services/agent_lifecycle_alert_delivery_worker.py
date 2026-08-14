import logging
import time

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.core import (
    AgentLifecycleAlertEvent,
    NotificationDestination,
)
from app.services.agent_lifecycle_alert_delivery_queue import (
    claim_due_agent_lifecycle_deliveries,
    mark_agent_lifecycle_delivery_canceled,
    mark_agent_lifecycle_delivery_delivered,
    mark_agent_lifecycle_delivery_failed,
)
from app.services.backup_alert_delivery_transport import (
    DeliveryPayload,
    deliver_webhook,
)
from app.services.notification_endpoint_policy import (
    validate_notification_endpoint,
)


logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 30
BATCH_SIZE = 20


def run_once() -> int:
    settings = get_settings()
    processed = 0

    with SessionLocal() as db:
        deliveries = claim_due_agent_lifecycle_deliveries(
            db,
            limit=BATCH_SIZE,
        )

        for delivery in deliveries:
            event = db.scalar(
                select(AgentLifecycleAlertEvent).where(
                    AgentLifecycleAlertEvent.id
                    == delivery.alert_event_id,
                    AgentLifecycleAlertEvent.workspace_id
                    == delivery.workspace_id,
                )
            )

            if event is None:
                mark_agent_lifecycle_delivery_failed(
                    db,
                    delivery=delivery,
                    error=(
                        "agent lifecycle alert event "
                        "not found"
                    ),
                )
                processed += 1
                continue

            destination = db.scalar(
                select(NotificationDestination).where(
                    NotificationDestination.id
                    == delivery.destination_id,
                    NotificationDestination.workspace_id
                    == delivery.workspace_id,
                )
            )

            if destination is None:
                mark_agent_lifecycle_delivery_canceled(
                    db,
                    delivery=delivery,
                    reason=(
                        "notification destination "
                        "not found"
                    ),
                )
                processed += 1
                continue

            if not destination.enabled:
                mark_agent_lifecycle_delivery_canceled(
                    db,
                    delivery=delivery,
                    reason=(
                        "notification destination "
                        "disabled"
                    ),
                )
                processed += 1
                continue

            if destination.channel != "webhook":
                mark_agent_lifecycle_delivery_canceled(
                    db,
                    delivery=delivery,
                    reason=(
                        "unsupported notification "
                        "channel: "
                        f"{destination.channel}"
                    ),
                )
                processed += 1
                continue

            try:
                validate_notification_endpoint(
                    destination.endpoint,
                    allow_private_networks=(
                        settings
                        .notification_webhook_allow_private_networks
                    ),
                )

                deliver_webhook(
                    url=destination.endpoint,
                    timeout_seconds=(
                        settings
                        .backup_alert_webhook_timeout_seconds
                    ),
                    signing_secret=(
                        settings
                        .notification_webhook_signing_secret
                    ),
                    payload=DeliveryPayload(
                        delivery_id=delivery.id,
                        workspace_id=delivery.workspace_id,
                        alert_event_id=event.id,
                        code=event.code,
                        severity=event.severity,
                        message=event.message,
                    ),
                )

                mark_agent_lifecycle_delivery_delivered(
                    db,
                    delivery=delivery,
                )

                logger.info(
                    "agent lifecycle alert delivered "
                    "delivery=%s event=%s",
                    delivery.id,
                    event.id,
                )

            except Exception as exc:
                mark_agent_lifecycle_delivery_failed(
                    db,
                    delivery=delivery,
                    error=exc,
                )

                logger.exception(
                    "agent lifecycle alert delivery "
                    "failed delivery=%s event=%s",
                    delivery.id,
                    event.id,
                )

            processed += 1

    return processed


def run_forever() -> None:
    logger.info(
        "agent lifecycle alert delivery worker started"
    )

    while True:
        try:
            run_once()
        except Exception:
            logger.exception(
                "agent lifecycle alert delivery "
                "iteration failed"
            )

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_forever()
