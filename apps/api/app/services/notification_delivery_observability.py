from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select
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



CLAIM_TIMEOUT_SECONDS = 300


@dataclass(frozen=True)
class NotificationDeliveryHealthCounts:
    total: int
    pending: int
    sending: int
    delivered: int
    failed: int
    canceled: int
    retryable_failed: int
    exhausted_failed: int
    stale_sending: int


@dataclass(frozen=True)
class NotificationDeliveryHealth:
    status: str
    issues: list[str]
    observed_at: datetime
    claim_timeout_seconds: int
    total: NotificationDeliveryHealthCounts
    backup: NotificationDeliveryHealthCounts
    agent_lifecycle: NotificationDeliveryHealthCounts


def _delivery_health_counts(
    db: Session,
    *,
    model,
    workspace_id: str,
    stale_before: datetime,
) -> NotificationDeliveryHealthCounts:
    row = db.execute(
        select(
            func.count(model.id).label("total"),
            func.sum(
                case((model.status == "pending", 1), else_=0)
            ).label("pending"),
            func.sum(
                case((model.status == "sending", 1), else_=0)
            ).label("sending"),
            func.sum(
                case((model.status == "delivered", 1), else_=0)
            ).label("delivered"),
            func.sum(
                case((model.status == "failed", 1), else_=0)
            ).label("failed"),
            func.sum(
                case((model.status == "canceled", 1), else_=0)
            ).label("canceled"),
            func.sum(
                case(
                    (
                        (model.status == "failed")
                        & (model.attempts < model.max_attempts),
                        1,
                    ),
                    else_=0,
                )
            ).label("retryable_failed"),
            func.sum(
                case(
                    (
                        (model.status == "failed")
                        & (model.attempts >= model.max_attempts),
                        1,
                    ),
                    else_=0,
                )
            ).label("exhausted_failed"),
            func.sum(
                case(
                    (
                        (model.status == "sending")
                        & (model.last_attempt_at <= stale_before),
                        1,
                    ),
                    else_=0,
                )
            ).label("stale_sending"),
        ).where(
            model.workspace_id == workspace_id
        )
    ).one()

    return NotificationDeliveryHealthCounts(
        total=int(row.total or 0),
        pending=int(row.pending or 0),
        sending=int(row.sending or 0),
        delivered=int(row.delivered or 0),
        failed=int(row.failed or 0),
        canceled=int(row.canceled or 0),
        retryable_failed=int(row.retryable_failed or 0),
        exhausted_failed=int(row.exhausted_failed or 0),
        stale_sending=int(row.stale_sending or 0),
    )


def _sum_health_counts(
    left: NotificationDeliveryHealthCounts,
    right: NotificationDeliveryHealthCounts,
) -> NotificationDeliveryHealthCounts:
    return NotificationDeliveryHealthCounts(
        total=left.total + right.total,
        pending=left.pending + right.pending,
        sending=left.sending + right.sending,
        delivered=left.delivered + right.delivered,
        failed=left.failed + right.failed,
        canceled=left.canceled + right.canceled,
        retryable_failed=(
            left.retryable_failed
            + right.retryable_failed
        ),
        exhausted_failed=(
            left.exhausted_failed
            + right.exhausted_failed
        ),
        stale_sending=(
            left.stale_sending
            + right.stale_sending
        ),
    )


def get_notification_delivery_health(
    db: Session,
    *,
    workspace_id: str,
    now: datetime | None = None,
) -> NotificationDeliveryHealth:
    now = now or datetime.now(timezone.utc)
    stale_before = now - timedelta(
        seconds=CLAIM_TIMEOUT_SECONDS
    )

    backup = _delivery_health_counts(
        db,
        model=BackupAlertDelivery,
        workspace_id=workspace_id,
        stale_before=stale_before,
    )

    agent_lifecycle = _delivery_health_counts(
        db,
        model=AgentLifecycleAlertDelivery,
        workspace_id=workspace_id,
        stale_before=stale_before,
    )

    total = _sum_health_counts(
        backup,
        agent_lifecycle,
    )

    issues: list[str] = []

    if total.retryable_failed:
        issues.append(
            "notification_delivery_retryable_failure"
        )

    if total.exhausted_failed:
        issues.append(
            "notification_delivery_retries_exhausted"
        )

    if total.stale_sending:
        issues.append(
            "notification_delivery_stale_sending"
        )

    return NotificationDeliveryHealth(
        status="degraded" if issues else "healthy",
        issues=issues,
        observed_at=now,
        claim_timeout_seconds=CLAIM_TIMEOUT_SECONDS,
        total=total,
        backup=backup,
        agent_lifecycle=agent_lifecycle,
    )



@dataclass(frozen=True)
class NotificationDeliveryProblemRecord(
    NotificationDeliveryRecord
):
    problem: str


def _problem_record(
    delivery,
    *,
    source: str,
    now: datetime,
) -> NotificationDeliveryProblemRecord | None:
    problem: str | None = None

    if delivery.status == "failed":
        if delivery.attempts >= delivery.max_attempts:
            problem = "exhausted_failed"
        else:
            problem = "retryable_failed"

    elif (
        delivery.status == "sending"
        and delivery.last_attempt_at is not None
        and delivery.last_attempt_at
        <= now - timedelta(seconds=CLAIM_TIMEOUT_SECONDS)
    ):
        problem = "stale_sending"

    if problem is None:
        return None

    base = _record(
        delivery,
        source=source,
    )

    return NotificationDeliveryProblemRecord(
        **base.__dict__,
        problem=problem,
    )


def list_notification_delivery_problems(
    db: Session,
    *,
    workspace_id: str,
    source: str | None = None,
    limit: int = 100,
    now: datetime | None = None,
) -> list[NotificationDeliveryProblemRecord]:
    now = now or datetime.now(timezone.utc)
    stale_before = now - timedelta(
        seconds=CLAIM_TIMEOUT_SECONDS
    )

    records: list[NotificationDeliveryProblemRecord] = []

    def load(model, source_name: str):
        statement = (
            select(model)
            .where(
                model.workspace_id == workspace_id,
                (
                    (
                        model.status == "failed"
                    )
                    | (
                        (model.status == "sending")
                        & (model.last_attempt_at.is_not(None))
                        & (model.last_attempt_at <= stale_before)
                    )
                ),
            )
            .order_by(
                model.created_at.desc(),
                model.id.desc(),
            )
            .limit(limit)
        )

        for delivery in db.scalars(statement).all():
            record = _problem_record(
                delivery,
                source=source_name,
                now=now,
            )

            if record is not None:
                records.append(record)

    if source in (None, SOURCE_BACKUP):
        load(
            BackupAlertDelivery,
            SOURCE_BACKUP,
        )

    if source in (None, SOURCE_AGENT_LIFECYCLE):
        load(
            AgentLifecycleAlertDelivery,
            SOURCE_AGENT_LIFECYCLE,
        )

    records.sort(
        key=lambda item: (
            item.created_at,
            item.id,
        ),
        reverse=True,
    )

    return records[:limit]
