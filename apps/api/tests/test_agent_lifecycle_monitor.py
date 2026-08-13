from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

from app.services.agent_lifecycle_monitor import (
    sync_all_agent_lifecycle_alerts,
    sync_workspace_agent_lifecycle_alerts,
)


def test_workspace_monitor_runs_diagnostics_evaluation_and_sync():
    db = MagicMock()
    db.scalars.return_value.all.return_value = []

    diagnostics = {
        "expired_pending_rotations": 1,
        "incomplete_pending_rotations": 0,
        "revoked_with_pending_rotation": 0,
    }

    alerts = [MagicMock()]
    events = [MagicMock()]

    with (
        patch(
            "app.services.agent_lifecycle_monitor."
            "get_agent_token_lifecycle_diagnostics",
            return_value=diagnostics,
        ) as get_diagnostics,
        patch(
            "app.services.agent_lifecycle_monitor."
            "evaluate_agent_lifecycle_alerts",
            return_value=alerts,
        ) as evaluate_alerts,
        patch(
            "app.services.agent_lifecycle_monitor."
            "sync_agent_lifecycle_alert_events",
            return_value=events,
        ) as sync_events,
        patch(
            "app.services.agent_lifecycle_monitor."
            "find_matching_destinations",
            return_value=[],
        ),
    ):
        result = sync_workspace_agent_lifecycle_alerts(
            db,
            workspace_id="workspace-1",
        )

    assert result == events

    get_diagnostics.assert_called_once_with(
        db,
        "workspace-1",
    )
    evaluate_alerts.assert_called_once_with(
        diagnostics
    )
    sync_events.assert_called_once_with(
        db,
        workspace_id="workspace-1",
        alerts=alerts,
    )


def test_new_lifecycle_event_is_routed_and_enqueued():
    db = MagicMock()
    db.scalars.return_value.all.return_value = []

    event = SimpleNamespace(
        id="event-1",
        workspace_id="workspace-1",
        code="agent_token_rotation_expired",
        severity="warning",
    )

    destination = SimpleNamespace(
        id="destination-1",
        channel="webhook",
    )

    with (
        patch(
            "app.services.agent_lifecycle_monitor."
            "get_agent_token_lifecycle_diagnostics",
            return_value={},
        ),
        patch(
            "app.services.agent_lifecycle_monitor."
            "evaluate_agent_lifecycle_alerts",
            return_value=[],
        ),
        patch(
            "app.services.agent_lifecycle_monitor."
            "sync_agent_lifecycle_alert_events",
            return_value=[event],
        ),
        patch(
            "app.services.agent_lifecycle_monitor."
            "find_matching_destinations",
            return_value=[destination],
        ) as find_destinations,
        patch(
            "app.services.agent_lifecycle_monitor."
            "enqueue_agent_lifecycle_alert_delivery",
        ) as enqueue_delivery,
    ):
        sync_workspace_agent_lifecycle_alerts(
            db,
            workspace_id="workspace-1",
        )

    find_destinations.assert_called_once_with(
        db,
        event=event,
    )

    enqueue_delivery.assert_called_once_with(
        db,
        workspace_id="workspace-1",
        alert_event_id="event-1",
        channel="webhook",
        destination_id="destination-1",
    )


def test_existing_active_lifecycle_event_is_not_reenqueued():
    db = MagicMock()
    db.scalars.return_value.all.return_value = [
        "agent_token_rotation_expired"
    ]

    event = SimpleNamespace(
        id="event-1",
        workspace_id="workspace-1",
        code="agent_token_rotation_expired",
        severity="warning",
    )

    with (
        patch(
            "app.services.agent_lifecycle_monitor."
            "get_agent_token_lifecycle_diagnostics",
            return_value={},
        ),
        patch(
            "app.services.agent_lifecycle_monitor."
            "evaluate_agent_lifecycle_alerts",
            return_value=[],
        ),
        patch(
            "app.services.agent_lifecycle_monitor."
            "sync_agent_lifecycle_alert_events",
            return_value=[event],
        ),
        patch(
            "app.services.agent_lifecycle_monitor."
            "find_matching_destinations",
        ) as find_destinations,
        patch(
            "app.services.agent_lifecycle_monitor."
            "enqueue_agent_lifecycle_alert_delivery",
        ) as enqueue_delivery,
    ):
        sync_workspace_agent_lifecycle_alerts(
            db,
            workspace_id="workspace-1",
        )

    find_destinations.assert_not_called()
    enqueue_delivery.assert_not_called()


def test_monitor_includes_agent_and_active_alert_workspaces():
    db = MagicMock()

    agent_result = MagicMock()
    agent_result.all.return_value = [
        "workspace-a",
        "workspace-b",
    ]

    alert_result = MagicMock()
    alert_result.all.return_value = [
        "workspace-b",
        "workspace-c",
    ]

    db.scalars.side_effect = [
        agent_result,
        alert_result,
    ]

    with patch(
        "app.services.agent_lifecycle_monitor."
        "sync_workspace_agent_lifecycle_alerts",
    ) as sync_workspace:
        result = sync_all_agent_lifecycle_alerts(db)

    assert result == 3

    assert sync_workspace.call_args_list == [
        call(db, workspace_id="workspace-a"),
        call(db, workspace_id="workspace-b"),
        call(db, workspace_id="workspace-c"),
    ]


def test_workspace_failure_does_not_block_other_workspaces():
    db = MagicMock()

    agent_result = MagicMock()
    agent_result.all.return_value = [
        "workspace-a",
        "workspace-b",
    ]

    alert_result = MagicMock()
    alert_result.all.return_value = []

    db.scalars.side_effect = [
        agent_result,
        alert_result,
    ]

    with (
        patch(
            "app.services.agent_lifecycle_monitor."
            "sync_workspace_agent_lifecycle_alerts",
            side_effect=[
                RuntimeError("workspace failed"),
                [],
            ],
        ) as sync_workspace,
        patch(
            "app.services.agent_lifecycle_monitor."
            "logger.exception",
        ) as log_exception,
    ):
        result = sync_all_agent_lifecycle_alerts(db)

    assert result == 1
    assert sync_workspace.call_count == 2

    db.rollback.assert_called_once()

    log_exception.assert_called_once_with(
        "agent lifecycle alert reconciliation failed",
        extra={"workspace_id": "workspace-a"},
    )
