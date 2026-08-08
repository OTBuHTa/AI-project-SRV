import logging
import time

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.core import BackupAlertEvent
from app.services.backup_alert_delivery_queue import (
    claim_due_deliveries,
    mark_delivery_delivered,
    mark_delivery_failed,
)
from app.services.backup_alert_delivery_transport import (
    DeliveryPayload,
    deliver_webhook,
)


logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 30
BATCH_SIZE = 20


def run_once() -> int:
    settings = get_settings()

    if not settings.backup_alert_webhook_url:
        logger.debug("backup alert webhook disabled")
        return 0

    processed = 0

    with SessionLocal() as db:
        deliveries = claim_due_deliveries(
            db,
            limit=BATCH_SIZE,
        )

        for delivery in deliveries:
            event = db.scalar(
                select(BackupAlertEvent).where(
                    BackupAlertEvent.id == delivery.alert_event_id,
                    BackupAlertEvent.workspace_id == delivery.workspace_id,
                )
            )

            if event is None:
                mark_delivery_failed(
                    db,
                    delivery=delivery,
                    error="backup alert event not found",
                )
                processed += 1
                continue

            try:
                deliver_webhook(
                    url=settings.backup_alert_webhook_url,
                    timeout_seconds=(
                        settings.backup_alert_webhook_timeout_seconds
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

                mark_delivery_delivered(
                    db,
                    delivery=delivery,
                )

                logger.info(
                    "backup alert delivered delivery=%s event=%s",
                    delivery.id,
                    event.id,
                )

            except Exception as exc:
                mark_delivery_failed(
                    db,
                    delivery=delivery,
                    error=exc,
                )

                logger.exception(
                    "backup alert delivery failed delivery=%s event=%s",
                    delivery.id,
                    event.id,
                )

            processed += 1

    return processed


def run_forever() -> None:
    logger.info("backup alert delivery worker started")

    while True:
        try:
            run_once()
        except Exception:
            logger.exception("backup alert delivery iteration failed")

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_forever()
