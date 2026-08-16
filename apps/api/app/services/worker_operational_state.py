from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import WorkerOperationalState


WORKER_BACKUP_SCHEDULER = "backup_scheduler"
WORKER_BACKUP_ALERT_DELIVERY = "backup_alert_delivery"
WORKER_AGENT_LIFECYCLE_ALERT_DELIVERY = (
    "agent_lifecycle_alert_delivery"
)

VALID_WORKERS = frozenset(
    {
        WORKER_BACKUP_SCHEDULER,
        WORKER_BACKUP_ALERT_DELIVERY,
        WORKER_AGENT_LIFECYCLE_ALERT_DELIVERY,
    }
)

MAX_ERROR_LENGTH = 4000


def _validate_worker_name(worker_name: str) -> None:
    if worker_name not in VALID_WORKERS:
        raise ValueError(
            f"invalid operational worker name: {worker_name}"
        )


def _normalized_now(
    now: datetime | None,
) -> datetime:
    value = now or datetime.now(timezone.utc)

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def _get_or_create_state(
    db: Session,
    *,
    worker_name: str,
) -> WorkerOperationalState:
    _validate_worker_name(worker_name)

    state = db.get(
        WorkerOperationalState,
        worker_name,
    )

    if state is None:
        state = WorkerOperationalState(
            worker_name=worker_name,
        )
        db.add(state)

    return state


def mark_worker_started(
    db: Session,
    *,
    worker_name: str,
    now: datetime | None = None,
) -> WorkerOperationalState:
    observed_at = _normalized_now(now)

    state = _get_or_create_state(
        db,
        worker_name=worker_name,
    )

    state.last_started_at = observed_at
    state.last_heartbeat_at = observed_at

    return state


def mark_worker_succeeded(
    db: Session,
    *,
    worker_name: str,
    processed_count: int,
    now: datetime | None = None,
) -> WorkerOperationalState:
    if processed_count < 0:
        raise ValueError(
            "worker processed_count must be non-negative"
        )

    observed_at = _normalized_now(now)

    state = _get_or_create_state(
        db,
        worker_name=worker_name,
    )

    state.last_completed_at = observed_at
    state.last_success_at = observed_at
    state.last_heartbeat_at = observed_at
    state.last_iteration_success = True
    state.last_processed_count = processed_count
    state.last_error = None

    return state


def mark_worker_failed(
    db: Session,
    *,
    worker_name: str,
    error: object,
    now: datetime | None = None,
) -> WorkerOperationalState:
    observed_at = _normalized_now(now)

    state = _get_or_create_state(
        db,
        worker_name=worker_name,
    )

    error_text = str(error)

    state.last_completed_at = observed_at
    state.last_failure_at = observed_at
    state.last_heartbeat_at = observed_at
    state.last_iteration_success = False
    state.last_error = error_text[:MAX_ERROR_LENGTH]

    return state


def list_worker_operational_states(
    db: Session,
) -> list[WorkerOperationalState]:
    return list(
        db.scalars(
            select(WorkerOperationalState).order_by(
                WorkerOperationalState.worker_name
            )
        ).all()
    )


def persist_worker_started(
    *,
    worker_name: str,
    session_factory,
    now: datetime | None = None,
) -> None:
    with session_factory() as db:
        mark_worker_started(
            db,
            worker_name=worker_name,
            now=now,
        )
        db.commit()


def persist_worker_succeeded(
    *,
    worker_name: str,
    processed_count: int,
    session_factory,
    now: datetime | None = None,
) -> None:
    with session_factory() as db:
        mark_worker_succeeded(
            db,
            worker_name=worker_name,
            processed_count=processed_count,
            now=now,
        )
        db.commit()


def persist_worker_failed(
    *,
    worker_name: str,
    error: object,
    session_factory,
    now: datetime | None = None,
) -> None:
    with session_factory() as db:
        mark_worker_failed(
            db,
            worker_name=worker_name,
            error=error,
            now=now,
        )
        db.commit()
