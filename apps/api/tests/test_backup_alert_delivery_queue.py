from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.backup_alert_delivery_queue import (
    DELIVERED,
    FAILED,
    PENDING,
    SENDING,
    calculate_backoff_seconds,
    claim_due_deliveries,
    enqueue_alert_delivery,
    mark_delivery_delivered,
    mark_delivery_failed,
)


def test_enqueue_delivery_is_idempotent():
    now = datetime(2026, 8, 9, tzinfo=timezone.utc)

    delivery = SimpleNamespace(
        alert_event_id="event-1",
        channel="webhook",
        status=PENDING,
    )

    db = MagicMock()
    db.scalar.return_value = delivery

    result = enqueue_alert_delivery(
        db,
        workspace_id="workspace-1",
        alert_event_id="event-1",
        channel="webhook",
        now=now,
    )

    assert result is delivery
    db.execute.assert_called_once()
    db.commit.assert_called_once()


def test_claim_due_delivery():
    now = datetime(2026, 8, 9, tzinfo=timezone.utc)

    delivery = SimpleNamespace(
        status=PENDING,
        attempts=0,
        max_attempts=5,
        last_attempt_at=None,
        updated_at=None,
    )

    db = MagicMock()
    db.scalars.return_value.all.return_value = [delivery]

    result = claim_due_deliveries(
        db,
        now=now,
        limit=10,
    )

    assert result == [delivery]
    assert delivery.status == SENDING
    assert delivery.attempts == 1
    assert delivery.last_attempt_at == now
    assert delivery.updated_at == now
    db.commit.assert_called_once()


def test_mark_delivery_delivered():
    now = datetime(2026, 8, 9, tzinfo=timezone.utc)

    delivery = SimpleNamespace(
        status=SENDING,
        delivered_at=None,
        next_attempt_at=now,
        last_error="old error",
        updated_at=None,
    )

    db = MagicMock()

    mark_delivery_delivered(
        db,
        delivery=delivery,
        now=now,
    )

    assert delivery.status == DELIVERED
    assert delivery.delivered_at == now
    assert delivery.next_attempt_at is None
    assert delivery.last_error is None
    db.commit.assert_called_once()


def test_failed_delivery_gets_exponential_backoff():
    now = datetime(2026, 8, 9, tzinfo=timezone.utc)

    delivery = SimpleNamespace(
        status=SENDING,
        attempts=2,
        max_attempts=5,
        next_attempt_at=None,
        last_error=None,
        updated_at=None,
    )

    db = MagicMock()

    mark_delivery_failed(
        db,
        delivery=delivery,
        error="network failure",
        now=now,
    )

    assert delivery.status == FAILED
    assert delivery.last_error == "network failure"
    assert delivery.next_attempt_at == now + timedelta(seconds=120)
    db.commit.assert_called_once()


def test_terminal_failure_has_no_next_attempt():
    now = datetime(2026, 8, 9, tzinfo=timezone.utc)

    delivery = SimpleNamespace(
        status=SENDING,
        attempts=5,
        max_attempts=5,
        next_attempt_at=now,
        last_error=None,
        updated_at=None,
    )

    db = MagicMock()

    mark_delivery_failed(
        db,
        delivery=delivery,
        error=RuntimeError("permanent failure"),
        now=now,
    )

    assert delivery.status == FAILED
    assert delivery.next_attempt_at is None


def test_backoff_is_capped():
    assert calculate_backoff_seconds(1) == 60
    assert calculate_backoff_seconds(2) == 120
    assert calculate_backoff_seconds(3) == 240
    assert calculate_backoff_seconds(20) == 3600


def test_stale_sending_delivery_can_be_reclaimed():
    now = datetime(2026, 8, 9, tzinfo=timezone.utc)

    delivery = SimpleNamespace(
        status=SENDING,
        attempts=1,
        max_attempts=5,
        last_attempt_at=now - timedelta(minutes=10),
        updated_at=None,
    )

    db = MagicMock()
    db.scalars.return_value.all.return_value = [delivery]

    result = claim_due_deliveries(
        db,
        now=now,
        limit=10,
    )

    assert result == [delivery]
    assert delivery.status == SENDING
    assert delivery.attempts == 2
    assert delivery.last_attempt_at == now
    assert delivery.updated_at == now
    db.commit.assert_called_once()
