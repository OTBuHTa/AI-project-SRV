from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

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


def test_problem_view_classifies_retryable_failure():
    from app.services.notification_delivery_observability import (
        list_notification_delivery_problems,
    )

    db = MagicMock()

    failed = delivery(
        "failed-1",
        status="failed",
        created_at=NOW,
    )
    failed.attempts = 2
    failed.max_attempts = 5

    db.scalars.side_effect = [
        scalar_result([failed]),
        scalar_result([]),
    ]

    result = list_notification_delivery_problems(
        db,
        workspace_id="workspace-1",
        now=NOW,
    )

    assert len(result) == 1
    assert result[0].id == "failed-1"
    assert result[0].problem == "retryable_failed"


def test_problem_view_classifies_exhausted_failure():
    from app.services.notification_delivery_observability import (
        list_notification_delivery_problems,
    )

    db = MagicMock()

    failed = delivery(
        "failed-1",
        status="failed",
        created_at=NOW,
    )
    failed.attempts = 5
    failed.max_attempts = 5

    db.scalars.side_effect = [
        scalar_result([]),
        scalar_result([failed]),
    ]

    result = list_notification_delivery_problems(
        db,
        workspace_id="workspace-1",
        now=NOW,
    )

    assert len(result) == 1
    assert result[0].problem == "exhausted_failed"


def test_problem_view_classifies_stale_sending():
    from app.services.notification_delivery_observability import (
        list_notification_delivery_problems,
    )

    db = MagicMock()

    sending = delivery(
        "sending-1",
        status="sending",
        created_at=NOW,
    )
    sending.last_attempt_at = (
        NOW - timedelta(seconds=301)
    )

    db.scalars.side_effect = [
        scalar_result([sending]),
        scalar_result([]),
    ]

    result = list_notification_delivery_problems(
        db,
        workspace_id="workspace-1",
        now=NOW,
    )

    assert len(result) == 1
    assert result[0].problem == "stale_sending"


def test_problem_view_excludes_normal_deliveries():
    from app.services.notification_delivery_observability import (
        list_notification_delivery_problems,
    )

    db = MagicMock()

    pending = delivery(
        "pending-1",
        status="pending",
        created_at=NOW,
    )

    sending = delivery(
        "sending-1",
        status="sending",
        created_at=NOW,
    )
    sending.last_attempt_at = (
        NOW - timedelta(seconds=60)
    )

    delivered = delivery(
        "delivered-1",
        status="delivered",
        created_at=NOW,
    )

    db.scalars.side_effect = [
        scalar_result(
            [pending, sending, delivered]
        ),
        scalar_result([]),
    ]

    result = list_notification_delivery_problems(
        db,
        workspace_id="workspace-1",
        now=NOW,
    )

    assert result == []


def test_problem_view_source_filter_queries_one_source():
    from app.services.notification_delivery_observability import (
        SOURCE_BACKUP,
        list_notification_delivery_problems,
    )

    db = MagicMock()

    db.scalars.return_value = scalar_result([])

    result = list_notification_delivery_problems(
        db,
        workspace_id="workspace-1",
        source=SOURCE_BACKUP,
        now=NOW,
    )

    assert result == []
    assert db.scalars.call_count == 1


def test_problem_view_is_workspace_scoped():
    from app.services.notification_delivery_observability import (
        list_notification_delivery_problems,
    )

    db = MagicMock()

    db.scalars.side_effect = [
        scalar_result([]),
        scalar_result([]),
    ]

    list_notification_delivery_problems(
        db,
        workspace_id="workspace-secret",
        now=NOW,
    )

    assert db.scalars.call_count == 2

    for call in db.scalars.call_args_list:
        statement = call.args[0]
        params = statement.compile().params

        assert "workspace-secret" in params.values()


def test_problem_view_applies_global_limit():
    from app.services.notification_delivery_observability import (
        list_notification_delivery_problems,
    )

    db = MagicMock()

    backup = delivery(
        "backup-failed",
        status="failed",
        created_at=NOW,
    )
    backup.attempts = 1
    backup.max_attempts = 5

    lifecycle = delivery(
        "lifecycle-failed",
        status="failed",
        created_at=NOW + timedelta(minutes=1),
    )
    lifecycle.attempts = 1
    lifecycle.max_attempts = 5

    db.scalars.side_effect = [
        scalar_result([backup]),
        scalar_result([lifecycle]),
    ]

    result = list_notification_delivery_problems(
        db,
        workspace_id="workspace-1",
        limit=1,
        now=NOW,
    )

    assert [item.id for item in result] == [
        "lifecycle-failed"
    ]


def test_backup_delivery_query_does_not_reference_lifecycle_table():
    db = MagicMock()
    db.scalars.return_value = scalar_result([])

    list_notification_deliveries(
        db,
        workspace_id="workspace-1",
        source=SOURCE_BACKUP,
        limit=25,
    )

    assert db.scalars.call_count == 1

    statement = db.scalars.call_args.args[0]
    sql = str(statement.compile())

    assert "backup_alert_deliveries" in sql
    assert "agent_lifecycle_alert_deliveries" not in sql


def test_delivery_history_applies_global_offset_after_merge():
    db = MagicMock()

    backup_new = delivery(
        "backup-new",
        created_at=NOW + timedelta(minutes=4),
    )
    backup_old = delivery(
        "backup-old",
        created_at=NOW + timedelta(minutes=1),
    )

    lifecycle_new = delivery(
        "lifecycle-new",
        created_at=NOW + timedelta(minutes=3),
    )
    lifecycle_old = delivery(
        "lifecycle-old",
        created_at=NOW + timedelta(minutes=2),
    )

    db.scalars.side_effect = [
        scalar_result([backup_new, backup_old]),
        scalar_result([lifecycle_new, lifecycle_old]),
    ]

    result = list_notification_deliveries(
        db,
        workspace_id="workspace-1",
        offset=1,
        limit=2,
    )

    assert [item.id for item in result] == [
        "lifecycle-new",
        "lifecycle-old",
    ]

    for call in db.scalars.call_args_list:
        statement = call.args[0]
        params = statement.compile().params

        # Each source is bounded by offset + limit.
        assert 3 in params.values()


def test_delivery_history_applies_extended_filters():
    db = MagicMock()

    db.scalars.side_effect = [
        scalar_result([]),
        scalar_result([]),
    ]

    created_from = NOW - timedelta(days=7)
    created_to = NOW

    list_notification_deliveries(
        db,
        workspace_id="workspace-1",
        destination_id="destination-1",
        channel="webhook",
        created_from=created_from,
        created_to=created_to,
        offset=5,
        limit=10,
    )

    assert db.scalars.call_count == 2

    for call in db.scalars.call_args_list:
        statement = call.args[0]
        params = statement.compile().params
        values = list(params.values())

        assert "workspace-1" in values
        assert "destination-1" in values
        assert "webhook" in values
        assert created_from in values
        assert created_to in values

        # offset + limit
        assert 15 in values


def test_delivery_history_filters_apply_to_both_sources():
    created_from = NOW - timedelta(hours=2)
    created_to = NOW + timedelta(hours=2)

    db = MagicMock()
    db.scalars.side_effect = [
        scalar_result([]),
        scalar_result([]),
    ]

    list_notification_deliveries(
        db,
        workspace_id="workspace-1",
        status="failed",
        destination_id="destination-1",
        channel="webhook",
        created_from=created_from,
        created_to=created_to,
        limit=25,
    )

    assert db.scalars.call_count == 2

    for call in db.scalars.call_args_list:
        statement = call.args[0]
        params = statement.compile().params
        values = set(params.values())

        assert "workspace-1" in values
        assert "failed" in values
        assert "destination-1" in values
        assert "webhook" in values
        assert created_from in values
        assert created_to in values
        assert 25 in values


def test_delivery_history_applies_offset_after_global_merge():
    db = MagicMock()

    backup_newest = delivery(
        "backup-newest",
        created_at=NOW + timedelta(minutes=4),
    )
    backup_older = delivery(
        "backup-older",
        created_at=NOW + timedelta(minutes=1),
    )

    lifecycle_new = delivery(
        "lifecycle-new",
        created_at=NOW + timedelta(minutes=3),
    )
    lifecycle_old = delivery(
        "lifecycle-old",
        created_at=NOW,
    )

    db.scalars.side_effect = [
        scalar_result([backup_newest, backup_older]),
        scalar_result([lifecycle_new, lifecycle_old]),
    ]

    result = list_notification_deliveries(
        db,
        workspace_id="workspace-1",
        offset=1,
        limit=2,
    )

    assert [item.id for item in result] == [
        "lifecycle-new",
        "backup-older",
    ]


def test_delivery_history_queries_cover_global_offset_window():
    db = MagicMock()
    db.scalars.side_effect = [
        scalar_result([]),
        scalar_result([]),
    ]

    list_notification_deliveries(
        db,
        workspace_id="workspace-1",
        offset=20,
        limit=25,
    )

    assert db.scalars.call_count == 2

    for call in db.scalars.call_args_list:
        statement = call.args[0]
        params = statement.compile().params

        # Each source must expose enough rows for the global
        # merge + offset operation: offset + limit = 45.
        assert 45 in params.values()


def test_problem_view_filters_retryable_failures_in_sql():
    from app.services.notification_delivery_observability import (
        list_notification_delivery_problems,
    )

    db = MagicMock()
    db.scalars.return_value = scalar_result([])

    list_notification_delivery_problems(
        db,
        workspace_id="workspace-1",
        source=SOURCE_BACKUP,
        problem="retryable_failed",
        now=NOW,
    )

    statement = db.scalars.call_args.args[0]
    sql = str(statement.compile())

    assert "backup_alert_deliveries" in sql
    assert "agent_lifecycle_alert_deliveries" not in sql
    assert "attempts <" in sql


def test_problem_view_applies_extended_filters():
    from app.services.notification_delivery_observability import (
        list_notification_delivery_problems,
    )

    created_from = NOW - timedelta(hours=1)
    created_to = NOW + timedelta(hours=1)

    db = MagicMock()
    db.scalars.side_effect = [
        scalar_result([]),
        scalar_result([]),
    ]

    list_notification_delivery_problems(
        db,
        workspace_id="workspace-1",
        destination_id="destination-1",
        channel="webhook",
        created_from=created_from,
        created_to=created_to,
        now=NOW,
    )

    assert db.scalars.call_count == 2

    for call in db.scalars.call_args_list:
        statement = call.args[0]
        values = set(statement.compile().params.values())

        assert "workspace-1" in values
        assert "destination-1" in values
        assert "webhook" in values
        assert created_from in values
        assert created_to in values


def test_problem_view_applies_offset_after_global_merge():
    from app.services.notification_delivery_observability import (
        list_notification_delivery_problems,
    )

    backup_new = delivery(
        "backup-new",
        status="failed",
        created_at=NOW + timedelta(minutes=4),
    )
    backup_new.attempts = 1
    backup_new.max_attempts = 5

    backup_old = delivery(
        "backup-old",
        status="failed",
        created_at=NOW + timedelta(minutes=1),
    )
    backup_old.attempts = 1
    backup_old.max_attempts = 5

    lifecycle_new = delivery(
        "lifecycle-new",
        status="failed",
        created_at=NOW + timedelta(minutes=3),
    )
    lifecycle_new.attempts = 1
    lifecycle_new.max_attempts = 5

    lifecycle_old = delivery(
        "lifecycle-old",
        status="failed",
        created_at=NOW,
    )
    lifecycle_old.attempts = 1
    lifecycle_old.max_attempts = 5

    db = MagicMock()
    db.scalars.side_effect = [
        scalar_result([backup_new, backup_old]),
        scalar_result([lifecycle_new, lifecycle_old]),
    ]

    result = list_notification_delivery_problems(
        db,
        workspace_id="workspace-1",
        offset=1,
        limit=2,
        now=NOW,
    )

    assert [item.id for item in result] == [
        "lifecycle-new",
        "backup-old",
    ]


def test_problem_view_queries_cover_global_offset_window():
    from app.services.notification_delivery_observability import (
        list_notification_delivery_problems,
    )

    db = MagicMock()
    db.scalars.side_effect = [
        scalar_result([]),
        scalar_result([]),
    ]

    list_notification_delivery_problems(
        db,
        workspace_id="workspace-1",
        offset=20,
        limit=25,
        now=NOW,
    )

    assert db.scalars.call_count == 2

    for call in db.scalars.call_args_list:
        statement = call.args[0]
        assert 45 in statement.compile().params.values()


def test_delivery_count_sums_both_sources():
    from app.services.notification_delivery_observability import (
        get_notification_delivery_count,
    )

    db = MagicMock()
    db.scalar.side_effect = [7, 5]

    result = get_notification_delivery_count(
        db,
        workspace_id="workspace-1",
    )

    assert result.total == 12
    assert result.backup == 7
    assert result.agent_lifecycle == 5
    assert db.scalar.call_count == 2


def test_delivery_count_respects_source_filter():
    from app.services.notification_delivery_observability import (
        get_notification_delivery_count,
    )

    db = MagicMock()
    db.scalar.return_value = 4

    result = get_notification_delivery_count(
        db,
        workspace_id="workspace-1",
        source=SOURCE_BACKUP,
    )

    assert result.total == 4
    assert result.backup == 4
    assert result.agent_lifecycle == 0
    assert db.scalar.call_count == 1

    sql = str(db.scalar.call_args.args[0].compile())

    assert "backup_alert_deliveries" in sql
    assert "agent_lifecycle_alert_deliveries" not in sql


def test_problem_count_sums_problem_records_only():
    from app.services.notification_delivery_observability import (
        get_notification_delivery_problem_count,
    )

    db = MagicMock()
    db.scalar.side_effect = [3, 2]

    result = get_notification_delivery_problem_count(
        db,
        workspace_id="workspace-1",
        now=NOW,
    )

    assert result.total == 5
    assert result.backup == 3
    assert result.agent_lifecycle == 2

    assert db.scalar.call_count == 2

    for call in db.scalar.call_args_list:
        compiled = call.args[0].compile()
        sql = str(compiled)
        values = set(compiled.params.values())

        assert (
            "backup_alert_deliveries" in sql
            or "agent_lifecycle_alert_deliveries" in sql
        )
        assert "failed" in values
        assert "sending" in values


def test_problem_count_respects_problem_filter():
    from app.services.notification_delivery_observability import (
        get_notification_delivery_problem_count,
    )

    db = MagicMock()
    db.scalar.return_value = 6

    result = get_notification_delivery_problem_count(
        db,
        workspace_id="workspace-1",
        source=SOURCE_AGENT_LIFECYCLE,
        problem="exhausted_failed",
        now=NOW,
    )

    assert result.total == 6
    assert result.backup == 0
    assert result.agent_lifecycle == 6
    assert db.scalar.call_count == 1

    sql = str(db.scalar.call_args.args[0].compile())

    assert "agent_lifecycle_alert_deliveries" in sql
    assert "backup_alert_deliveries" not in sql


def test_delivery_cursor_page_uses_stable_global_order():
    from app.services.notification_delivery_observability import (
        SOURCE_AGENT_LIFECYCLE,
        SOURCE_BACKUP,
        decode_notification_delivery_cursor,
        list_notification_deliveries_page,
    )

    db = MagicMock()

    backup_a = delivery(
        "backup-z",
        created_at=NOW,
    )
    backup_b = delivery(
        "backup-a",
        created_at=NOW,
    )
    lifecycle = delivery(
        "lifecycle-z",
        created_at=NOW,
    )

    db.scalars.side_effect = [
        scalar_result([backup_a, backup_b]),
        scalar_result([lifecycle]),
    ]

    page = list_notification_deliveries_page(
        db,
        workspace_id="workspace-1",
        limit=2,
    )

    assert [
        (item.source, item.id)
        for item in page.items
    ] == [
        (SOURCE_BACKUP, "backup-z"),
        (SOURCE_BACKUP, "backup-a"),
    ]

    assert page.has_more is True
    assert page.next_cursor is not None

    cursor = decode_notification_delivery_cursor(
        page.next_cursor
    )

    assert cursor.source == SOURCE_BACKUP
    assert cursor.id == "backup-a"

    for call in db.scalars.call_args_list:
        params = call.args[0].compile().params
        assert 3 in params.values()


def test_delivery_cursor_page_does_not_repeat_boundary():
    from app.services.notification_delivery_observability import (
        list_notification_deliveries_page,
    )

    first_db = MagicMock()

    boundary = delivery(
        "backup-z",
        created_at=NOW,
    )
    older = delivery(
        "backup-a",
        created_at=NOW - timedelta(minutes=1),
    )

    first_db.scalars.side_effect = [
        scalar_result([boundary, older]),
        scalar_result([]),
    ]

    first_page = list_notification_deliveries_page(
        first_db,
        workspace_id="workspace-1",
        limit=1,
    )

    assert first_page.next_cursor is not None
    assert first_page.items[0].id == "backup-z"

    second_db = MagicMock()
    second_db.scalars.side_effect = [
        scalar_result([boundary, older]),
        scalar_result([]),
    ]

    second_page = list_notification_deliveries_page(
        second_db,
        workspace_id="workspace-1",
        cursor=first_page.next_cursor,
        limit=10,
    )

    assert [item.id for item in second_page.items] == [
        "backup-a"
    ]


def test_delivery_cursor_rejects_filter_mismatch():
    from app.services.notification_delivery_observability import (
        NotificationDeliveryCursorError,
        list_notification_deliveries_page,
    )

    db = MagicMock()
    db.scalars.side_effect = [
        scalar_result(
            [
                delivery(
                    "backup-2",
                    created_at=NOW,
                ),
                delivery(
                    "backup-1",
                    created_at=NOW - timedelta(minutes=1),
                ),
            ]
        ),
        scalar_result([]),
    ]

    page = list_notification_deliveries_page(
        db,
        workspace_id="workspace-1",
        limit=1,
    )

    assert page.next_cursor is not None

    with pytest.raises(NotificationDeliveryCursorError):
        list_notification_deliveries_page(
            MagicMock(),
            workspace_id="workspace-1",
            source="backup",
            cursor=page.next_cursor,
            limit=1,
        )


def test_delivery_cursor_preserves_source_isolation():
    from app.services.notification_delivery_observability import (
        SOURCE_BACKUP,
        list_notification_deliveries_page,
    )

    db = MagicMock()
    db.scalars.return_value = scalar_result(
        [delivery("backup-1")]
    )

    page = list_notification_deliveries_page(
        db,
        workspace_id="workspace-1",
        source=SOURCE_BACKUP,
        limit=10,
    )

    assert len(page.items) == 1
    assert page.items[0].source == SOURCE_BACKUP
    assert db.scalars.call_count == 1


def test_problem_cursor_preserves_observation_snapshot():
    from app.services.notification_delivery_observability import (
        decode_notification_delivery_cursor,
        list_notification_delivery_problems_page,
    )

    first_db = MagicMock()

    failed_new = delivery(
        "failed-new",
        status="failed",
        created_at=NOW,
    )
    failed_old = delivery(
        "failed-old",
        status="failed",
        created_at=NOW - timedelta(minutes=1),
    )

    first_db.scalars.side_effect = [
        scalar_result([failed_new, failed_old]),
        scalar_result([]),
    ]

    first_page = list_notification_delivery_problems_page(
        first_db,
        workspace_id="workspace-1",
        limit=1,
        now=NOW,
    )

    assert first_page.has_more is True
    assert first_page.next_cursor is not None
    assert first_page.observed_at == NOW

    cursor = decode_notification_delivery_cursor(
        first_page.next_cursor
    )

    assert cursor.snapshot_at == NOW

    second_db = MagicMock()
    second_db.scalars.side_effect = [
        scalar_result([failed_old]),
        scalar_result([]),
    ]

    second_page = list_notification_delivery_problems_page(
        second_db,
        workspace_id="workspace-1",
        cursor=first_page.next_cursor,
        limit=10,
        now=NOW + timedelta(hours=1),
    )

    assert second_page.observed_at == NOW
    assert [item.id for item in second_page.items] == [
        "failed-old"
    ]


def test_problem_page_rejects_history_cursor():
    from app.services.notification_delivery_observability import (
        NotificationDeliveryCursorError,
        list_notification_deliveries_page,
        list_notification_delivery_problems_page,
    )

    history_db = MagicMock()
    history_db.scalars.side_effect = [
        scalar_result(
            [
                delivery(
                    "backup-2",
                    created_at=NOW,
                ),
                delivery(
                    "backup-1",
                    created_at=NOW - timedelta(minutes=1),
                ),
            ]
        ),
        scalar_result([]),
    ]

    history_page = list_notification_deliveries_page(
        history_db,
        workspace_id="workspace-1",
        limit=1,
    )

    with pytest.raises(NotificationDeliveryCursorError):
        list_notification_delivery_problems_page(
            MagicMock(),
            workspace_id="workspace-1",
            cursor=history_page.next_cursor,
            limit=1,
            now=NOW,
        )


def test_delivery_cursor_preserves_history_snapshot():
    from app.services.notification_delivery_observability import (
        decode_notification_delivery_cursor,
        list_notification_deliveries_page,
    )

    first_db = MagicMock()

    first_db.scalars.side_effect = [
        scalar_result(
            [
                delivery(
                    "backup-2",
                    created_at=NOW,
                ),
                delivery(
                    "backup-1",
                    created_at=NOW - timedelta(minutes=1),
                ),
            ]
        ),
        scalar_result([]),
    ]

    first_page = list_notification_deliveries_page(
        first_db,
        workspace_id="workspace-1",
        limit=1,
        now=NOW + timedelta(minutes=5),
    )

    assert first_page.has_more is True
    assert first_page.next_cursor is not None
    assert (
        first_page.observed_at
        == NOW + timedelta(minutes=5)
    )

    cursor = decode_notification_delivery_cursor(
        first_page.next_cursor
    )

    assert (
        cursor.snapshot_at
        == NOW + timedelta(minutes=5)
    )

    second_db = MagicMock()
    second_db.scalars.side_effect = [
        scalar_result(
            [
                delivery(
                    "backup-1",
                    created_at=NOW - timedelta(minutes=1),
                )
            ]
        ),
        scalar_result([]),
    ]

    second_page = list_notification_deliveries_page(
        second_db,
        workspace_id="workspace-1",
        cursor=first_page.next_cursor,
        limit=10,
        now=NOW + timedelta(hours=2),
    )

    assert (
        second_page.observed_at
        == first_page.observed_at
    )
    assert [item.id for item in second_page.items] == [
        "backup-1"
    ]


def test_delivery_cursor_crosses_source_at_same_timestamp():
    from app.services.notification_delivery_observability import (
        SOURCE_AGENT_LIFECYCLE,
        SOURCE_BACKUP,
        list_notification_deliveries_page,
    )

    first_db = MagicMock()

    first_db.scalars.side_effect = [
        scalar_result(
            [
                delivery(
                    "backup-z",
                    created_at=NOW,
                ),
                delivery(
                    "backup-a",
                    created_at=NOW,
                ),
            ]
        ),
        scalar_result(
            [
                delivery(
                    "lifecycle-z",
                    created_at=NOW,
                )
            ]
        ),
    ]

    first_page = list_notification_deliveries_page(
        first_db,
        workspace_id="workspace-1",
        limit=2,
        now=NOW + timedelta(minutes=1),
    )

    assert [
        (item.source, item.id)
        for item in first_page.items
    ] == [
        (SOURCE_BACKUP, "backup-z"),
        (SOURCE_BACKUP, "backup-a"),
    ]

    assert first_page.next_cursor is not None

    second_db = MagicMock()
    second_db.scalars.side_effect = [
        scalar_result([]),
        scalar_result(
            [
                delivery(
                    "lifecycle-z",
                    created_at=NOW,
                )
            ]
        ),
    ]

    second_page = list_notification_deliveries_page(
        second_db,
        workspace_id="workspace-1",
        cursor=first_page.next_cursor,
        limit=10,
    )

    assert [
        (item.source, item.id)
        for item in second_page.items
    ] == [
        (
            SOURCE_AGENT_LIFECYCLE,
            "lifecycle-z",
        )
    ]


def test_operational_snapshot_reports_source_counts_and_pending_age():
    from app.services.notification_delivery_observability import (
        get_notification_delivery_operational_snapshot,
    )

    db = MagicMock()

    db.execute.side_effect = [
        execute_result(
            health_row(
                total=5,
                pending=2,
                sending=1,
                delivered=1,
                failed=1,
                retryable_failed=1,
            )
        ),
        execute_result(
            health_row(
                total=4,
                delivered=2,
                failed=1,
                canceled=1,
                exhausted_failed=1,
            )
        ),
    ]

    db.scalar.side_effect = [
        NOW - timedelta(seconds=120),
        None,
    ]

    result = get_notification_delivery_operational_snapshot(
        db,
        now=NOW,
    )

    assert result.observed_at == NOW

    assert result.backup.counts.total == 5
    assert result.backup.counts.pending == 2
    assert result.backup.counts.retryable_failed == 1
    assert result.backup.oldest_pending_age_seconds == 120.0

    assert result.agent_lifecycle.counts.total == 4
    assert result.agent_lifecycle.counts.delivered == 2
    assert result.agent_lifecycle.counts.exhausted_failed == 1
    assert (
        result.agent_lifecycle.oldest_pending_age_seconds
        == 0.0
    )

    assert db.execute.call_count == 2
    assert db.scalar.call_count == 2


def test_operational_snapshot_uses_claim_timeout_for_stale_sending():
    from app.services.notification_delivery_observability import (
        get_notification_delivery_operational_snapshot,
    )

    db = MagicMock()

    db.execute.side_effect = [
        execute_result(health_row()),
        execute_result(health_row()),
    ]

    db.scalar.side_effect = [None, None]

    get_notification_delivery_operational_snapshot(
        db,
        now=NOW,
    )

    expected_cutoff = NOW - timedelta(seconds=300)

    for call in db.execute.call_args_list:
        statement = call.args[0]
        params = statement.compile().params

        assert expected_cutoff in params.values()
