from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import (
    AgentLifecycleAlertDelivery,
    BackupAlertDelivery,
)


SOURCE_BACKUP = "backup"
SOURCE_AGENT_LIFECYCLE = "agent_lifecycle"

VALID_SOURCES = {
    SOURCE_BACKUP,
    SOURCE_AGENT_LIFECYCLE,
}

VALID_STATUSES = {
    "pending",
    "sending",
    "delivered",
    "failed",
    "canceled",
}


@dataclass(frozen=True)
class NotificationDeliveryRecord:
    id: str
    source: str
    workspace_id: str
    alert_event_id: str
    channel: str
    destination_id: str | None
    status: str
    attempts: int
    max_attempts: int
    next_attempt_at: datetime | None
    last_attempt_at: datetime | None
    delivered_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime


def _record(
    delivery,
    *,
    source: str,
) -> NotificationDeliveryRecord:
    return NotificationDeliveryRecord(
        id=delivery.id,
        source=source,
        workspace_id=delivery.workspace_id,
        alert_event_id=delivery.alert_event_id,
        channel=delivery.channel,
        destination_id=delivery.destination_id,
        status=delivery.status,
        attempts=delivery.attempts,
        max_attempts=delivery.max_attempts,
        next_attempt_at=delivery.next_attempt_at,
        last_attempt_at=delivery.last_attempt_at,
        delivered_at=delivery.delivered_at,
        last_error=delivery.last_error,
        created_at=delivery.created_at,
        updated_at=delivery.updated_at,
    )


def list_notification_deliveries(
    db: Session,
    *,
    workspace_id: str,
    source: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[NotificationDeliveryRecord]:
    records: list[NotificationDeliveryRecord] = []

    if source in (None, SOURCE_BACKUP):
        statement = select(BackupAlertDelivery).where(
            BackupAlertDelivery.workspace_id == workspace_id
        )

        if status is not None:
            statement = statement.where(
                BackupAlertDelivery.status == status
            )

        statement = (
            statement
            .order_by(
                BackupAlertDelivery.created_at.desc(),
                BackupAlertDelivery.id.desc(),
            )
            .limit(limit)
        )

        statement = (
            statement
            .order_by(
                AgentLifecycleAlertDelivery.created_at.desc(),
                AgentLifecycleAlertDelivery.id.desc(),
            )
            .limit(limit)
        )

        statement = (
            statement
            .order_by(
                BackupAlertDelivery.created_at.desc(),
                BackupAlertDelivery.id.desc(),
            )
            .limit(limit)
        )

        deliveries = db.scalars(statement).all()

        records.extend(
            _record(
                delivery,
                source=SOURCE_BACKUP,
            )
            for delivery in deliveries
        )

    if source in (None, SOURCE_AGENT_LIFECYCLE):
        statement = select(
            AgentLifecycleAlertDelivery
        ).where(
            AgentLifecycleAlertDelivery.workspace_id
            == workspace_id
        )

        if status is not None:
            statement = statement.where(
                AgentLifecycleAlertDelivery.status == status
            )

        statement = (
            statement
            .order_by(
                AgentLifecycleAlertDelivery.created_at.desc(),
                AgentLifecycleAlertDelivery.id.desc(),
            )
            .limit(limit)
        )

        deliveries = db.scalars(statement).all()

        records.extend(
            _record(
                delivery,
                source=SOURCE_AGENT_LIFECYCLE,
            )
            for delivery in deliveries
        )

    records.sort(
        key=lambda item: (
            item.created_at,
            item.id,
        ),
        reverse=True,
    )

    return records[:limit]
