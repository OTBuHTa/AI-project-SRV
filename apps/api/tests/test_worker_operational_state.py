from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.models.core import WorkerOperationalState
from app.services.worker_operational_state import (
    MAX_ERROR_LENGTH,
    WORKER_BACKUP_ALERT_DELIVERY,
    WORKER_BACKUP_SCHEDULER,
    mark_worker_failed,
    mark_worker_started,
    mark_worker_succeeded,
)


NOW = datetime(
    2026,
    8,
    16,
    1,
    0,
    tzinfo=timezone.utc,
)


def test_worker_start_creates_state_and_heartbeat():
    db = MagicMock()
    db.get.return_value = None

    result = mark_worker_started(
        db,
        worker_name=WORKER_BACKUP_SCHEDULER,
        now=NOW,
    )

    assert isinstance(
        result,
        WorkerOperationalState,
    )
    assert result.worker_name == WORKER_BACKUP_SCHEDULER
    assert result.last_started_at == NOW
    assert result.last_heartbeat_at == NOW

    db.add.assert_called_once_with(result)


def test_worker_success_updates_operational_state():
    db = MagicMock()

    state = WorkerOperationalState(
        worker_name=WORKER_BACKUP_ALERT_DELIVERY,
    )
    state.last_error = "old error"

    db.get.return_value = state

    result = mark_worker_succeeded(
        db,
        worker_name=WORKER_BACKUP_ALERT_DELIVERY,
        processed_count=7,
        now=NOW,
    )

    assert result.last_completed_at == NOW
    assert result.last_success_at == NOW
    assert result.last_heartbeat_at == NOW
    assert result.last_iteration_success is True
    assert result.last_processed_count == 7
    assert result.last_error is None


def test_worker_failure_records_bounded_error():
    db = MagicMock()

    state = WorkerOperationalState(
        worker_name=WORKER_BACKUP_ALERT_DELIVERY,
    )

    db.get.return_value = state

    result = mark_worker_failed(
        db,
        worker_name=WORKER_BACKUP_ALERT_DELIVERY,
        error="x" * (MAX_ERROR_LENGTH + 100),
        now=NOW,
    )

    assert result.last_completed_at == NOW
    assert result.last_failure_at == NOW
    assert result.last_heartbeat_at == NOW
    assert result.last_iteration_success is False
    assert len(result.last_error) == MAX_ERROR_LENGTH


def test_invalid_worker_name_is_rejected():
    db = MagicMock()

    with pytest.raises(
        ValueError,
        match="invalid operational worker name",
    ):
        mark_worker_started(
            db,
            worker_name="workspace-secret-worker",
            now=NOW,
        )

    db.get.assert_not_called()


def test_negative_processed_count_is_rejected():
    db = MagicMock()

    with pytest.raises(
        ValueError,
        match="processed_count",
    ):
        mark_worker_succeeded(
            db,
            worker_name=WORKER_BACKUP_SCHEDULER,
            processed_count=-1,
            now=NOW,
        )
