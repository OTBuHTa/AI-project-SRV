import logging
import time

from sqlalchemy import select

from app.core.config import get_settings
from app.core.startup_security import (
    validate_production_build_identity,
)
from app.db.session import SessionLocal
from app.models.core import BackupAlertEvent, NotificationDestination
from app.services.backup_alert_delivery_queue import (
    claim_due_deliveries,
    mark_delivery_canceled,
    mark_delivery_delivered,
    mark_delivery_failed,
)
from app.services.backup_alert_delivery_transport import (
    DeliveryPayload,
    deliver_webhook,
)
from app.services.notification_endpoint_policy import (
    validate_notification_endpoint,
)
from app.services.worker_operational_state import (
    WORKER_BACKUP_ALERT_DELIVERY,
    persist_worker_failed,
    persist_worker_started,
    persist_worker_succeeded,
)

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 30
BATCH_SIZE = 20


def run_once() -> int:
    settings = get_settings()

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

            destination = db.scalar(
                select(NotificationDestination).where(
                    NotificationDestination.id
                    == delivery.destination_id,
                    NotificationDestination.workspace_id
                    == delivery.workspace_id,
                )
            )

            if destination is None:
                mark_delivery_canceled(
                    db,
                    delivery=delivery,
                    reason="notification destination not found",
                )
                processed += 1
                continue

            if not destination.enabled:
                mark_delivery_canceled(
                    db,
                    delivery=delivery,
                    reason="notification destination disabled",
                )
                processed += 1
                continue

            if destination.channel != "webhook":
                mark_delivery_canceled(
                    db,
                    delivery=delivery,
                    reason=(
                        "unsupported notification channel: "
                        f"{destination.channel}"
                    ),
                )
                processed += 1
                continue

            try:
                validate_notification_endpoint(
                    destination.endpoint,
                    allow_private_networks=(
                        settings.notification_webhook_allow_private_networks
                    ),
                )

                deliver_webhook(
                    url=destination.endpoint,
                    timeout_seconds=(
                        settings.backup_alert_webhook_timeout_seconds
                    ),
                    signing_secret=(
                        settings.notification_webhook_signing_secret
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

def _record_started() -> None:
    try:
        persist_worker_started(
            worker_name=WORKER_BACKUP_ALERT_DELIVERY,
            session_factory=SessionLocal,
        )
    except Exception:
        logger.exception(
            "backup delivery observability start write failed"
        )


def _record_succeeded(processed: int) -> None:
    try:
        persist_worker_succeeded(
            worker_name=WORKER_BACKUP_ALERT_DELIVERY,
            processed_count=processed,
            session_factory=SessionLocal,
        )
    except Exception:
        logger.exception(
            "backup delivery observability success write failed"
        )


def _record_failed(error: object) -> None:
    try:
        persist_worker_failed(
            worker_name=WORKER_BACKUP_ALERT_DELIVERY,
            error=error,
            session_factory=SessionLocal,
        )
    except Exception:
        logger.exception(
            "backup delivery observability failure write failed"
        )


def run_forever() -> None:
    validate_production_build_identity(get_settings())

    logger.info("backup alert delivery worker started")

    while True:
        _record_started()

        try:
            processed = run_once()
        except Exception as exc:
            _record_failed(exc)
            logger.exception(
                "backup alert delivery iteration failed"
            )
        else:
            _record_succeeded(processed)

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_forever()
