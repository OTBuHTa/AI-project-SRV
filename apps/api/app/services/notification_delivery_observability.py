import base64
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, or_, select
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


VALID_PROBLEMS = {
    "retryable_failed",
    "exhausted_failed",
    "stale_sending",
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
    destination_id: str | None = None,
    channel: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    offset: int = 0,
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

        if destination_id is not None:
            statement = statement.where(
                BackupAlertDelivery.destination_id
                == destination_id
            )

        if channel is not None:
            statement = statement.where(
                BackupAlertDelivery.channel == channel
            )

        if created_from is not None:
            statement = statement.where(
                BackupAlertDelivery.created_at
                >= created_from
            )

        if created_to is not None:
            statement = statement.where(
                BackupAlertDelivery.created_at
                <= created_to
            )

        statement = (
            statement
            .order_by(
                BackupAlertDelivery.created_at.desc(),
                BackupAlertDelivery.id.desc(),
            )
            .limit(offset + limit)
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

        if destination_id is not None:
            statement = statement.where(
                AgentLifecycleAlertDelivery.destination_id
                == destination_id
            )

        if channel is not None:
            statement = statement.where(
                AgentLifecycleAlertDelivery.channel == channel
            )

        if created_from is not None:
            statement = statement.where(
                AgentLifecycleAlertDelivery.created_at
                >= created_from
            )

        if created_to is not None:
            statement = statement.where(
                AgentLifecycleAlertDelivery.created_at
                <= created_to
            )

        statement = (
            statement
            .order_by(
                AgentLifecycleAlertDelivery.created_at.desc(),
                AgentLifecycleAlertDelivery.id.desc(),
            )
            .limit(offset + limit)
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

    return records[offset:offset + limit]



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


def _problem_query_condition(
    model,
    *,
    problem: str | None,
    stale_before: datetime,
):
    retryable_failed = (
        (model.status == "failed")
        & (model.attempts < model.max_attempts)
    )

    exhausted_failed = (
        (model.status == "failed")
        & (model.attempts >= model.max_attempts)
    )

    stale_sending = (
        (model.status == "sending")
        & (model.last_attempt_at.is_not(None))
        & (model.last_attempt_at <= stale_before)
    )

    if problem == "retryable_failed":
        return retryable_failed

    if problem == "exhausted_failed":
        return exhausted_failed

    if problem == "stale_sending":
        return stale_sending

    return (
        retryable_failed
        | exhausted_failed
        | stale_sending
    )


def list_notification_delivery_problems(
    db: Session,
    *,
    workspace_id: str,
    source: str | None = None,
    problem: str | None = None,
    destination_id: str | None = None,
    channel: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    offset: int = 0,
    limit: int = 100,
    now: datetime | None = None,
) -> list[NotificationDeliveryProblemRecord]:
    now = now or datetime.now(timezone.utc)

    stale_before = now - timedelta(
        seconds=CLAIM_TIMEOUT_SECONDS
    )

    records: list[NotificationDeliveryProblemRecord] = []

    def load(model, source_name: str):
        statement = select(model).where(
            model.workspace_id == workspace_id,
            _problem_query_condition(
                model,
                problem=problem,
                stale_before=stale_before,
            ),
        )

        if destination_id is not None:
            statement = statement.where(
                model.destination_id == destination_id
            )

        if channel is not None:
            statement = statement.where(
                model.channel == channel
            )

        if created_from is not None:
            statement = statement.where(
                model.created_at >= created_from
            )

        if created_to is not None:
            statement = statement.where(
                model.created_at <= created_to
            )

        statement = (
            statement
            .order_by(
                model.created_at.desc(),
                model.id.desc(),
            )
            .limit(offset + limit)
        )

        for delivery in db.scalars(statement).all():
            record = _problem_record(
                delivery,
                source=source_name,
                now=now,
            )

            if (
                record is not None
                and (
                    problem is None
                    or record.problem == problem
                )
            ):
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

    return records[offset:offset + limit]


@dataclass(frozen=True)
class NotificationDeliveryCount:
    total: int
    backup: int
    agent_lifecycle: int


def _count_deliveries(
    db: Session,
    *,
    model,
    workspace_id: str,
    status: str | None = None,
    destination_id: str | None = None,
    channel: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    problem: str | None = None,
    stale_before: datetime | None = None,
) -> int:
    statement = select(func.count(model.id)).where(
        model.workspace_id == workspace_id
    )

    if status is not None:
        statement = statement.where(
            model.status == status
        )

    if destination_id is not None:
        statement = statement.where(
            model.destination_id == destination_id
        )

    if channel is not None:
        statement = statement.where(
            model.channel == channel
        )

    if created_from is not None:
        statement = statement.where(
            model.created_at >= created_from
        )

    if created_to is not None:
        statement = statement.where(
            model.created_at <= created_to
        )

    if stale_before is not None:
        statement = statement.where(
            _problem_query_condition(
                model,
                problem=problem,
                stale_before=stale_before,
            )
        )

    return int(db.scalar(statement) or 0)


def get_notification_delivery_count(
    db: Session,
    *,
    workspace_id: str,
    source: str | None = None,
    status: str | None = None,
    destination_id: str | None = None,
    channel: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
) -> NotificationDeliveryCount:
    backup = 0
    agent_lifecycle = 0

    if source in (None, SOURCE_BACKUP):
        backup = _count_deliveries(
            db,
            model=BackupAlertDelivery,
            workspace_id=workspace_id,
            status=status,
            destination_id=destination_id,
            channel=channel,
            created_from=created_from,
            created_to=created_to,
        )

    if source in (None, SOURCE_AGENT_LIFECYCLE):
        agent_lifecycle = _count_deliveries(
            db,
            model=AgentLifecycleAlertDelivery,
            workspace_id=workspace_id,
            status=status,
            destination_id=destination_id,
            channel=channel,
            created_from=created_from,
            created_to=created_to,
        )

    return NotificationDeliveryCount(
        total=backup + agent_lifecycle,
        backup=backup,
        agent_lifecycle=agent_lifecycle,
    )


def get_notification_delivery_problem_count(
    db: Session,
    *,
    workspace_id: str,
    source: str | None = None,
    problem: str | None = None,
    destination_id: str | None = None,
    channel: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    now: datetime | None = None,
) -> NotificationDeliveryCount:
    now = now or datetime.now(timezone.utc)

    stale_before = now - timedelta(
        seconds=CLAIM_TIMEOUT_SECONDS
    )

    backup = 0
    agent_lifecycle = 0

    if source in (None, SOURCE_BACKUP):
        backup = _count_deliveries(
            db,
            model=BackupAlertDelivery,
            workspace_id=workspace_id,
            destination_id=destination_id,
            channel=channel,
            created_from=created_from,
            created_to=created_to,
            problem=problem,
            stale_before=stale_before,
        )

    if source in (None, SOURCE_AGENT_LIFECYCLE):
        agent_lifecycle = _count_deliveries(
            db,
            model=AgentLifecycleAlertDelivery,
            workspace_id=workspace_id,
            destination_id=destination_id,
            channel=channel,
            created_from=created_from,
            created_to=created_to,
            problem=problem,
            stale_before=stale_before,
        )

    return NotificationDeliveryCount(
        total=backup + agent_lifecycle,
        backup=backup,
        agent_lifecycle=agent_lifecycle,
    )

CURSOR_VERSION = 1
CURSOR_SCOPE_HISTORY = "history"
CURSOR_SCOPE_PROBLEMS = "problems"

VALID_CURSOR_SCOPES = {
    CURSOR_SCOPE_HISTORY,
    CURSOR_SCOPE_PROBLEMS,
}


class NotificationDeliveryCursorError(ValueError):
    pass


@dataclass(frozen=True)
class NotificationDeliveryCursor:
    scope: str
    created_at: datetime
    source: str
    id: str
    filter_hash: str
    snapshot_at: datetime | None = None


@dataclass(frozen=True)
class NotificationDeliveryPage:
    items: list[NotificationDeliveryRecord]
    next_cursor: str | None
    has_more: bool
    observed_at: datetime


@dataclass(frozen=True)
class NotificationDeliveryProblemPage:
    items: list[NotificationDeliveryProblemRecord]
    next_cursor: str | None
    has_more: bool
    observed_at: datetime


def _normalized_cursor_datetime(value: datetime) -> datetime:
    if value.utcoffset() is None:
        raise NotificationDeliveryCursorError(
            "cursor datetime must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _cursor_datetime_text(value: datetime) -> str:
    return _normalized_cursor_datetime(value).isoformat()


def _filter_value(value):
    if isinstance(value, datetime):
        return _cursor_datetime_text(value)

    return value


def _delivery_filter_hash(
    scope: str,
    **filters,
) -> str:
    payload = {
        "scope": scope,
        "filters": {
            key: _filter_value(filters[key])
            for key in sorted(filters)
        },
    }

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def encode_notification_delivery_cursor(
    cursor: NotificationDeliveryCursor,
) -> str:
    if cursor.scope not in VALID_CURSOR_SCOPES:
        raise NotificationDeliveryCursorError(
            "invalid cursor scope"
        )

    if cursor.source not in VALID_SOURCES:
        raise NotificationDeliveryCursorError(
            "invalid cursor source"
        )

    if not cursor.id:
        raise NotificationDeliveryCursorError(
            "invalid cursor id"
        )

    if len(cursor.filter_hash) != 64:
        raise NotificationDeliveryCursorError(
            "invalid cursor filter hash"
        )

    payload = {
        "v": CURSOR_VERSION,
        "scope": cursor.scope,
        "created_at": _cursor_datetime_text(
            cursor.created_at
        ),
        "source": cursor.source,
        "id": cursor.id,
        "filter_hash": cursor.filter_hash,
        "snapshot_at": (
            _cursor_datetime_text(cursor.snapshot_at)
            if cursor.snapshot_at is not None
            else None
        ),
    }

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return base64.urlsafe_b64encode(encoded).decode(
        "ascii"
    ).rstrip("=")


def _parse_cursor_datetime(
    value,
    *,
    field: str,
) -> datetime:
    if not isinstance(value, str):
        raise NotificationDeliveryCursorError(
            f"invalid cursor {field}"
        )

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise NotificationDeliveryCursorError(
            f"invalid cursor {field}"
        ) from exc

    return _normalized_cursor_datetime(parsed)


def decode_notification_delivery_cursor(
    value: str,
) -> NotificationDeliveryCursor:
    if not value or len(value) > 4096:
        raise NotificationDeliveryCursorError(
            "invalid notification delivery cursor"
        )

    try:
        padding = "=" * (-len(value) % 4)
        raw = base64.b64decode(
            value + padding,
            altchars=b"-_",
            validate=True,
        )
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise NotificationDeliveryCursorError(
            "invalid notification delivery cursor"
        ) from exc

    if not isinstance(payload, dict):
        raise NotificationDeliveryCursorError(
            "invalid notification delivery cursor"
        )

    if payload.get("v") != CURSOR_VERSION:
        raise NotificationDeliveryCursorError(
            "unsupported cursor version"
        )

    scope = payload.get("scope")
    source = payload.get("source")
    delivery_id = payload.get("id")
    filter_hash = payload.get("filter_hash")

    if scope not in VALID_CURSOR_SCOPES:
        raise NotificationDeliveryCursorError(
            "invalid cursor scope"
        )

    if source not in VALID_SOURCES:
        raise NotificationDeliveryCursorError(
            "invalid cursor source"
        )

    if not isinstance(delivery_id, str) or not delivery_id:
        raise NotificationDeliveryCursorError(
            "invalid cursor id"
        )

    if (
        not isinstance(filter_hash, str)
        or len(filter_hash) != 64
    ):
        raise NotificationDeliveryCursorError(
            "invalid cursor filter hash"
        )

    snapshot_raw = payload.get("snapshot_at")

    snapshot_at = (
        _parse_cursor_datetime(
            snapshot_raw,
            field="snapshot_at",
        )
        if snapshot_raw is not None
        else None
    )

    return NotificationDeliveryCursor(
        scope=scope,
        created_at=_parse_cursor_datetime(
            payload.get("created_at"),
            field="created_at",
        ),
        source=source,
        id=delivery_id,
        filter_hash=filter_hash,
        snapshot_at=snapshot_at,
    )


def _delivery_sort_key(record):
    return (
        record.created_at,
        record.source,
        record.id,
    )


def _record_is_after_cursor(
    record,
    cursor: NotificationDeliveryCursor,
) -> bool:
    return _delivery_sort_key(record) < (
        cursor.created_at,
        cursor.source,
        cursor.id,
    )


def _delivery_cursor_condition(
    model,
    *,
    source_name: str,
    cursor: NotificationDeliveryCursor,
):
    older_created = (
        model.created_at < cursor.created_at
    )

    if source_name < cursor.source:
        return or_(
            older_created,
            model.created_at == cursor.created_at,
        )

    if source_name == cursor.source:
        return or_(
            older_created,
            (
                (model.created_at == cursor.created_at)
                & (model.id < cursor.id)
            ),
        )

    return older_created


def _validate_page_cursor(
    cursor_value: str | None,
    *,
    scope: str,
    filter_hash: str,
) -> NotificationDeliveryCursor | None:
    if cursor_value is None:
        return None

    cursor = decode_notification_delivery_cursor(
        cursor_value
    )

    if cursor.scope != scope:
        raise NotificationDeliveryCursorError(
            "cursor scope mismatch"
        )

    if cursor.filter_hash != filter_hash:
        raise NotificationDeliveryCursorError(
            "cursor filter mismatch"
        )

    return cursor


def list_notification_deliveries_page(
    db: Session,
    *,
    workspace_id: str,
    source: str | None = None,
    status: str | None = None,
    destination_id: str | None = None,
    channel: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    cursor: str | None = None,
    limit: int = 100,
    now: datetime | None = None,
) -> NotificationDeliveryPage:
    if limit < 1:
        raise ValueError("limit must be positive")

    filter_hash = _delivery_filter_hash(
        CURSOR_SCOPE_HISTORY,
        workspace_id=workspace_id,
        source=source,
        status=status,
        destination_id=destination_id,
        channel=channel,
        created_from=created_from,
        created_to=created_to,
    )

    decoded_cursor = _validate_page_cursor(
        cursor,
        scope=CURSOR_SCOPE_HISTORY,
        filter_hash=filter_hash,
    )

    if decoded_cursor is not None:
        if decoded_cursor.snapshot_at is None:
            raise NotificationDeliveryCursorError(
                "history cursor missing snapshot"
            )

        observed_at = decoded_cursor.snapshot_at
    else:
        observed_at = now or datetime.now(timezone.utc)
        observed_at = _normalized_cursor_datetime(
            observed_at
        )

    records: list[NotificationDeliveryRecord] = []

    def load(model, source_name: str) -> None:
        statement = select(model).where(
            model.workspace_id == workspace_id
        )

        if status is not None:
            statement = statement.where(
                model.status == status
            )

        if destination_id is not None:
            statement = statement.where(
                model.destination_id == destination_id
            )

        if channel is not None:
            statement = statement.where(
                model.channel == channel
            )

        if created_from is not None:
            statement = statement.where(
                model.created_at >= created_from
            )

        if created_to is not None:
            statement = statement.where(
                model.created_at <= created_to
            )

        statement = statement.where(
            model.created_at <= observed_at
        )

        if decoded_cursor is not None:
            statement = statement.where(
                _delivery_cursor_condition(
                    model,
                    source_name=source_name,
                    cursor=decoded_cursor,
                )
            )

        statement = (
            statement
            .order_by(
                model.created_at.desc(),
                model.id.desc(),
            )
            .limit(limit + 1)
        )

        for delivery in db.scalars(statement).all():
            record = _record(
                delivery,
                source=source_name,
            )

            if (
                decoded_cursor is None
                or _record_is_after_cursor(
                    record,
                    decoded_cursor,
                )
            ):
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
        key=_delivery_sort_key,
        reverse=True,
    )

    items = records[:limit]
    has_more = len(records) > limit

    next_cursor = None

    if has_more and items:
        last = items[-1]

        next_cursor = encode_notification_delivery_cursor(
            NotificationDeliveryCursor(
                scope=CURSOR_SCOPE_HISTORY,
                created_at=last.created_at,
                source=last.source,
                id=last.id,
                filter_hash=filter_hash,
                snapshot_at=observed_at,
            )
        )

    return NotificationDeliveryPage(
        items=items,
        next_cursor=next_cursor,
        has_more=has_more,
        observed_at=observed_at,
    )


def list_notification_delivery_problems_page(
    db: Session,
    *,
    workspace_id: str,
    source: str | None = None,
    problem: str | None = None,
    destination_id: str | None = None,
    channel: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    cursor: str | None = None,
    limit: int = 100,
    now: datetime | None = None,
) -> NotificationDeliveryProblemPage:
    if limit < 1:
        raise ValueError("limit must be positive")

    filter_hash = _delivery_filter_hash(
        CURSOR_SCOPE_PROBLEMS,
        workspace_id=workspace_id,
        source=source,
        problem=problem,
        destination_id=destination_id,
        channel=channel,
        created_from=created_from,
        created_to=created_to,
    )

    decoded_cursor = _validate_page_cursor(
        cursor,
        scope=CURSOR_SCOPE_PROBLEMS,
        filter_hash=filter_hash,
    )

    if decoded_cursor is not None:
        if decoded_cursor.snapshot_at is None:
            raise NotificationDeliveryCursorError(
                "problem cursor missing snapshot"
            )

        observed_at = decoded_cursor.snapshot_at
    else:
        observed_at = now or datetime.now(timezone.utc)
        observed_at = _normalized_cursor_datetime(
            observed_at
        )

    stale_before = observed_at - timedelta(
        seconds=CLAIM_TIMEOUT_SECONDS
    )

    records: list[
        NotificationDeliveryProblemRecord
    ] = []

    def load(model, source_name: str) -> None:
        statement = select(model).where(
            model.workspace_id == workspace_id,
            _problem_query_condition(
                model,
                problem=problem,
                stale_before=stale_before,
            ),
        )

        if destination_id is not None:
            statement = statement.where(
                model.destination_id == destination_id
            )

        if channel is not None:
            statement = statement.where(
                model.channel == channel
            )

        if created_from is not None:
            statement = statement.where(
                model.created_at >= created_from
            )

        if created_to is not None:
            statement = statement.where(
                model.created_at <= created_to
            )

        if decoded_cursor is not None:
            statement = statement.where(
                _delivery_cursor_condition(
                    model,
                    source_name=source_name,
                    cursor=decoded_cursor,
                )
            )

        statement = (
            statement
            .order_by(
                model.created_at.desc(),
                model.id.desc(),
            )
            .limit(limit + 1)
        )

        for delivery in db.scalars(statement).all():
            record = _problem_record(
                delivery,
                source=source_name,
                now=observed_at,
            )

            if (
                record is not None
                and (
                    problem is None
                    or record.problem == problem
                )
                and (
                    decoded_cursor is None
                    or _record_is_after_cursor(
                        record,
                        decoded_cursor,
                    )
                )
            ):
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
        key=_delivery_sort_key,
        reverse=True,
    )

    items = records[:limit]
    has_more = len(records) > limit

    next_cursor = None

    if has_more and items:
        last = items[-1]

        next_cursor = encode_notification_delivery_cursor(
            NotificationDeliveryCursor(
                scope=CURSOR_SCOPE_PROBLEMS,
                created_at=last.created_at,
                source=last.source,
                id=last.id,
                filter_hash=filter_hash,
                snapshot_at=observed_at,
            )
        )

    return NotificationDeliveryProblemPage(
        items=items,
        next_cursor=next_cursor,
        has_more=has_more,
        observed_at=observed_at,
    )


@dataclass(frozen=True)
class NotificationDeliveryOperationalSource:
    counts: NotificationDeliveryHealthCounts
    oldest_pending_age_seconds: float


@dataclass(frozen=True)
class NotificationDeliveryOperationalSnapshot:
    observed_at: datetime
    backup: NotificationDeliveryOperationalSource
    agent_lifecycle: NotificationDeliveryOperationalSource


def _global_delivery_health_counts(
    db: Session,
    *,
    model,
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
                        & (model.last_attempt_at.is_not(None))
                        & (model.last_attempt_at <= stale_before),
                        1,
                    ),
                    else_=0,
                )
            ).label("stale_sending"),
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


def _oldest_pending_age_seconds(
    db: Session,
    *,
    model,
    now: datetime,
) -> float:
    oldest = db.scalar(
        select(func.min(model.created_at)).where(
            model.status == "pending"
        )
    )

    if oldest is None:
        return 0.0

    if oldest.tzinfo is None:
        oldest = oldest.replace(tzinfo=timezone.utc)

    age = (
        now.astimezone(timezone.utc)
        - oldest.astimezone(timezone.utc)
    ).total_seconds()

    return max(0.0, age)


def get_notification_delivery_operational_snapshot(
    db: Session,
    *,
    now: datetime | None = None,
) -> NotificationDeliveryOperationalSnapshot:
    now = now or datetime.now(timezone.utc)

    stale_before = now - timedelta(
        seconds=CLAIM_TIMEOUT_SECONDS
    )

    backup = NotificationDeliveryOperationalSource(
        counts=_global_delivery_health_counts(
            db,
            model=BackupAlertDelivery,
            stale_before=stale_before,
        ),
        oldest_pending_age_seconds=(
            _oldest_pending_age_seconds(
                db,
                model=BackupAlertDelivery,
                now=now,
            )
        ),
    )

    agent_lifecycle = NotificationDeliveryOperationalSource(
        counts=_global_delivery_health_counts(
            db,
            model=AgentLifecycleAlertDelivery,
            stale_before=stale_before,
        ),
        oldest_pending_age_seconds=(
            _oldest_pending_age_seconds(
                db,
                model=AgentLifecycleAlertDelivery,
                now=now,
            )
        ),
    )

    return NotificationDeliveryOperationalSnapshot(
        observed_at=now,
        backup=backup,
        agent_lifecycle=agent_lifecycle,
    )
