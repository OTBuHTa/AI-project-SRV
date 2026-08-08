from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.core import BackupAlertDelivery


PENDING = "pending"
SENDING = "sending"
DELIVERED = "delivered"
FAILED = "failed"

DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_BATCH_SIZE = 20
BASE_BACKOFF_SECONDS = 60
MAX_BACKOFF_SECONDS = 3600
CLAIM_TIMEOUT_SECONDS = 300


def enqueue_alert_delivery(
    db: Session,
    *,
    workspace_id: str,
    alert_event_id: str,
    channel: str,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    now: datetime | None = None,
) -> BackupAlertDelivery:
    now = now or datetime.now(timezone.utc)

    statement = (
        insert(BackupAlertDelivery)
        .values(
            id=str(uuid4()),
            workspace_id=workspace_id,
            alert_event_id=alert_event_id,
            channel=channel,
            status=PENDING,
            attempts=0,
            max_attempts=max_attempts,
            next_attempt_at=now,
            created_at=now,
            updated_at=now,
        )
        .on_conflict_do_nothing(
            constraint="uq_backup_alert_delivery_event_channel"
        )
    )

    db.execute(statement)
    db.commit()

    delivery = db.scalar(
        select(BackupAlertDelivery).where(
            BackupAlertDelivery.alert_event_id == alert_event_id,
            BackupAlertDelivery.channel == channel,
        )
    )

    if delivery is None:
        raise RuntimeError("failed to enqueue backup alert delivery")

    return delivery


def claim_due_deliveries(
    db: Session,
    *,
    now: datetime | None = None,
    limit: int = DEFAULT_BATCH_SIZE,
) -> list[BackupAlertDelivery]:
    now = now or datetime.now(timezone.utc)

    stale_before = now - timedelta(
        seconds=CLAIM_TIMEOUT_SECONDS
    )

    deliveries = list(
        db.scalars(
            select(BackupAlertDelivery)
            .where(
                BackupAlertDelivery.attempts
                < BackupAlertDelivery.max_attempts,
                or_(
                    (
                        BackupAlertDelivery.status.in_(
                            [PENDING, FAILED]
                        )
                    )
                    & or_(
                        BackupAlertDelivery.next_attempt_at.is_(None),
                        BackupAlertDelivery.next_attempt_at <= now,
                    ),
                    (
                        BackupAlertDelivery.status == SENDING
                    )
                    & (
                        BackupAlertDelivery.last_attempt_at
                        <= stale_before
                    ),
                ),
            )
            .order_by(
                BackupAlertDelivery.next_attempt_at.asc().nullsfirst(),
                BackupAlertDelivery.created_at.asc(),
            )
            .limit(limit)
            .with_for_update(skip_locked=True)
        ).all()
    )

    for delivery in deliveries:
        delivery.status = SENDING
        delivery.attempts += 1
        delivery.last_attempt_at = now
        delivery.updated_at = now

    db.commit()

    return deliveries


def mark_delivery_delivered(
    db: Session,
    *,
    delivery: BackupAlertDelivery,
    now: datetime | None = None,
) -> None:
    now = now or datetime.now(timezone.utc)

    delivery.status = DELIVERED
    delivery.delivered_at = now
    delivery.next_attempt_at = None
    delivery.last_error = None
    delivery.updated_at = now

    db.commit()


def calculate_backoff_seconds(
    attempts: int,
) -> int:
    if attempts <= 0:
        return BASE_BACKOFF_SECONDS

    seconds = BASE_BACKOFF_SECONDS * (2 ** (attempts - 1))

    return min(seconds, MAX_BACKOFF_SECONDS)


def mark_delivery_failed(
    db: Session,
    *,
    delivery: BackupAlertDelivery,
    error: Exception | str,
    now: datetime | None = None,
) -> None:
    now = now or datetime.now(timezone.utc)

    delivery.status = FAILED
    delivery.last_error = str(error)
    delivery.updated_at = now

    if delivery.attempts >= delivery.max_attempts:
        delivery.next_attempt_at = None
    else:
        delivery.next_attempt_at = now + timedelta(
            seconds=calculate_backoff_seconds(
                delivery.attempts
            )
        )

    db.commit()
