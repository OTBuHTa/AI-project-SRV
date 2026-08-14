from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.notification_delivery_observability import (
    SOURCE_AGENT_LIFECYCLE,
    SOURCE_BACKUP,
    list_notification_deliveries,
)


NOW = datetime(2026, 8, 14, 9, 0, tzinfo=timezone.utc)


def delivery(
    delivery_id: str,
    *,
    workspace_id: str = "workspace-1",
    status: str = "pending",
    created_at: datetime = NOW,
):
    return SimpleNamespace(
        id=delivery_id,
        workspace_id=workspace_id,
        alert_event_id=f"event-{delivery_id}",
        channel="webhook",
        destination_id=f"destination-{delivery_id}",
        status=status,
        attempts=1,
        max_attempts=5,
        next_attempt_at=None,
        last_attempt_at=None,
        delivered_at=None,
        last_error=None,
        created_at=created_at,
        updated_at=created_at,
    )


def scalar_result(items):
    result = MagicMock()
    result.all.return_value = items
    return result


def test_combines_backup_and_lifecycle_deliveries():
    db = MagicMock()

    backup = delivery(
        "backup-1",
        created_at=NOW,
    )
    lifecycle = delivery(
        "lifecycle-1",
        created_at=NOW + timedelta(minutes=1),
    )

    db.scalars.side_effect = [
        scalar_result([backup]),
        scalar_result([lifecycle]),
    ]

    result = list_notification_deliveries(
        db,
        workspace_id="workspace-1",
    )

    assert [
        (item.source, item.id)
        for item in result
    ] == [
        (
            SOURCE_AGENT_LIFECYCLE,
            "lifecycle-1",
        ),
        (
            SOURCE_BACKUP,
            "backup-1",
        ),
    ]

    assert db.scalars.call_count == 2


def test_backup_source_queries_only_backup():
    db = MagicMock()
    db.scalars.return_value = scalar_result(
        [delivery("backup-1")]
    )

    result = list_notification_deliveries(
        db,
        workspace_id="workspace-1",
        source=SOURCE_BACKUP,
    )

    assert len(result) == 1
    assert result[0].source == SOURCE_BACKUP
    assert db.scalars.call_count == 1


def test_lifecycle_source_queries_only_lifecycle():
    db = MagicMock()
    db.scalars.return_value = scalar_result(
        [delivery("lifecycle-1")]
    )

    result = list_notification_deliveries(
        db,
        workspace_id="workspace-1",
        source=SOURCE_AGENT_LIFECYCLE,
    )

    assert len(result) == 1
    assert result[0].source == SOURCE_AGENT_LIFECYCLE
    assert db.scalars.call_count == 1


def test_status_filter_is_applied_to_queries():
    db = MagicMock()

    db.scalars.side_effect = [
        scalar_result([]),
        scalar_result([]),
    ]

    list_notification_deliveries(
        db,
        workspace_id="workspace-1",
        status="failed",
    )

    assert db.scalars.call_count == 2

    for call in db.scalars.call_args_list:
        statement = call.args[0]
        params = statement.compile().params

        assert "workspace-1" in params.values()
        assert "failed" in params.values()


def test_workspace_filter_is_applied_to_both_sources():
    db = MagicMock()

    db.scalars.side_effect = [
        scalar_result([]),
        scalar_result([]),
    ]

    list_notification_deliveries(
        db,
        workspace_id="workspace-secret",
    )

    assert db.scalars.call_count == 2

    for call in db.scalars.call_args_list:
        statement = call.args[0]
        params = statement.compile().params

        assert "workspace-secret" in params.values()


def test_results_are_sorted_newest_first():
    db = MagicMock()

    older = delivery(
        "older",
        created_at=NOW,
    )
    newer = delivery(
        "newer",
        created_at=NOW + timedelta(minutes=2),
    )

    db.scalars.side_effect = [
        scalar_result([older]),
        scalar_result([newer]),
    ]

    result = list_notification_deliveries(
        db,
        workspace_id="workspace-1",
    )

    assert [item.id for item in result] == [
        "newer",
        "older",
    ]


def test_global_limit_is_applied_after_sources_are_merged():
    db = MagicMock()

    db.scalars.side_effect = [
        scalar_result(
            [
                delivery(
                    "backup-1",
                    created_at=NOW,
                ),
                delivery(
                    "backup-2",
                    created_at=NOW
                    - timedelta(minutes=1),
                ),
            ]
        ),
        scalar_result(
            [
                delivery(
                    "lifecycle-1",
                    created_at=NOW
                    + timedelta(minutes=1),
                ),
            ]
        ),
    ]

    result = list_notification_deliveries(
        db,
        workspace_id="workspace-1",
        limit=2,
    )

    assert [item.id for item in result] == [
        "lifecycle-1",
        "backup-1",
    ]

    for call in db.scalars.call_args_list:
        statement = call.args[0]
        params = statement.compile().params
        assert 2 in params.values()
