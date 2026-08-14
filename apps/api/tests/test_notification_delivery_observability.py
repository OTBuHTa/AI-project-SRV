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


def health_row(
    *,
    total=0,
    pending=0,
    sending=0,
    delivered=0,
    failed=0,
    canceled=0,
    retryable_failed=0,
    exhausted_failed=0,
    stale_sending=0,
):
    return SimpleNamespace(
        total=total,
        pending=pending,
        sending=sending,
        delivered=delivered,
        failed=failed,
        canceled=canceled,
        retryable_failed=retryable_failed,
        exhausted_failed=exhausted_failed,
        stale_sending=stale_sending,
    )


def execute_result(row):
    result = MagicMock()
    result.one.return_value = row
    return result


def test_delivery_health_is_healthy_without_failures():
    from app.services.notification_delivery_observability import (
        get_notification_delivery_health,
    )

    db = MagicMock()

    db.execute.side_effect = [
        execute_result(
            health_row(
                total=3,
                pending=1,
                sending=1,
                delivered=1,
            )
        ),
        execute_result(
            health_row(
                total=2,
                delivered=2,
            )
        ),
    ]

    result = get_notification_delivery_health(
        db,
        workspace_id="workspace-1",
        now=NOW,
    )

    assert result.status == "healthy"
    assert result.issues == []
    assert result.observed_at == NOW
    assert result.claim_timeout_seconds == 300

    assert result.total.total == 5
    assert result.total.pending == 1
    assert result.total.sending == 1
    assert result.total.delivered == 3

    assert result.backup.total == 3
    assert result.agent_lifecycle.total == 2


def test_retryable_failure_degrades_delivery_health():
    from app.services.notification_delivery_observability import (
        get_notification_delivery_health,
    )

    db = MagicMock()

    db.execute.side_effect = [
        execute_result(
            health_row(
                total=1,
                failed=1,
                retryable_failed=1,
            )
        ),
        execute_result(health_row()),
    ]

    result = get_notification_delivery_health(
        db,
        workspace_id="workspace-1",
        now=NOW,
    )

    assert result.status == "degraded"
    assert result.issues == [
        "notification_delivery_retryable_failure"
    ]

    assert result.total.failed == 1
    assert result.total.retryable_failed == 1
    assert result.total.exhausted_failed == 0


def test_exhausted_failure_degrades_delivery_health():
    from app.services.notification_delivery_observability import (
        get_notification_delivery_health,
    )

    db = MagicMock()

    db.execute.side_effect = [
        execute_result(health_row()),
        execute_result(
            health_row(
                total=1,
                failed=1,
                exhausted_failed=1,
            )
        ),
    ]

    result = get_notification_delivery_health(
        db,
        workspace_id="workspace-1",
        now=NOW,
    )

    assert result.status == "degraded"
    assert result.issues == [
        "notification_delivery_retries_exhausted"
    ]

    assert result.total.failed == 1
    assert result.total.exhausted_failed == 1


def test_stale_sending_degrades_delivery_health():
    from app.services.notification_delivery_observability import (
        get_notification_delivery_health,
    )

    db = MagicMock()

    db.execute.side_effect = [
        execute_result(
            health_row(
                total=1,
                sending=1,
                stale_sending=1,
            )
        ),
        execute_result(health_row()),
    ]

    result = get_notification_delivery_health(
        db,
        workspace_id="workspace-1",
        now=NOW,
    )

    assert result.status == "degraded"
    assert result.issues == [
        "notification_delivery_stale_sending"
    ]

    assert result.total.sending == 1
    assert result.total.stale_sending == 1


def test_delivery_health_aggregates_all_issue_types():
    from app.services.notification_delivery_observability import (
        get_notification_delivery_health,
    )

    db = MagicMock()

    db.execute.side_effect = [
        execute_result(
            health_row(
                total=2,
                failed=2,
                retryable_failed=1,
                exhausted_failed=1,
            )
        ),
        execute_result(
            health_row(
                total=1,
                sending=1,
                stale_sending=1,
            )
        ),
    ]

    result = get_notification_delivery_health(
        db,
        workspace_id="workspace-1",
        now=NOW,
    )

    assert result.status == "degraded"

    assert result.issues == [
        "notification_delivery_retryable_failure",
        "notification_delivery_retries_exhausted",
        "notification_delivery_stale_sending",
    ]

    assert result.total.total == 3
    assert result.total.failed == 2
    assert result.total.retryable_failed == 1
    assert result.total.exhausted_failed == 1
    assert result.total.stale_sending == 1


def test_delivery_health_queries_are_workspace_scoped():
    from app.services.notification_delivery_observability import (
        get_notification_delivery_health,
    )

    db = MagicMock()

    db.execute.side_effect = [
        execute_result(health_row()),
        execute_result(health_row()),
    ]

    get_notification_delivery_health(
        db,
        workspace_id="workspace-secret",
        now=NOW,
    )

    assert db.execute.call_count == 2

    for call in db.execute.call_args_list:
        statement = call.args[0]
        params = statement.compile().params

        assert "workspace-secret" in params.values()


def test_delivery_health_uses_claim_timeout_cutoff():
    from app.services.notification_delivery_observability import (
        get_notification_delivery_health,
    )

    db = MagicMock()

    db.execute.side_effect = [
        execute_result(health_row()),
        execute_result(health_row()),
    ]

    get_notification_delivery_health(
        db,
        workspace_id="workspace-1",
        now=NOW,
    )

    expected_cutoff = NOW - timedelta(seconds=300)

    for call in db.execute.call_args_list:
        statement = call.args[0]
        params = statement.compile().params

        assert expected_cutoff in params.values()
