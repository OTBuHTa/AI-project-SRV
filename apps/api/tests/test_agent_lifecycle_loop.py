from unittest.mock import MagicMock, patch

from app.main import _run_agent_lifecycle_iteration


def _sessions():
    return (
        MagicMock(),
        MagicMock(),
        MagicMock(),
    )


def test_status_failure_does_not_block_remaining_operations():
    status_db, alert_db, cleanup_db = _sessions()

    with (
        patch(
            "app.main.SessionLocal",
            side_effect=[
                status_db,
                alert_db,
                cleanup_db,
            ],
        ),
        patch(
            "app.main.evaluate_agent_statuses",
            side_effect=RuntimeError("status failed"),
        ) as evaluate_statuses,
        patch(
            "app.main.cleanup_expired_pending_rotations",
        ) as cleanup_rotations,
        patch(
            "app.main.sync_all_agent_lifecycle_alerts",
        ) as sync_alerts,
        patch(
            "app.main.logger.exception",
        ) as log_exception,
    ):
        _run_agent_lifecycle_iteration()

    evaluate_statuses.assert_called_once_with(
        status_db.__enter__.return_value
    )
    cleanup_rotations.assert_called_once_with(
        cleanup_db.__enter__.return_value
    )
    sync_alerts.assert_called_once_with(
        alert_db.__enter__.return_value
    )

    log_exception.assert_called_once_with(
        "agent status evaluation failed"
    )


def test_cleanup_failure_does_not_escape_iteration():
    status_db, alert_db, cleanup_db = _sessions()

    with (
        patch(
            "app.main.SessionLocal",
            side_effect=[
                status_db,
                alert_db,
                cleanup_db,
            ],
        ),
        patch(
            "app.main.evaluate_agent_statuses",
        ),
        patch(
            "app.main.cleanup_expired_pending_rotations",
            side_effect=RuntimeError("cleanup failed"),
        ),
        patch(
            "app.main.sync_all_agent_lifecycle_alerts",
        ) as sync_alerts,
        patch(
            "app.main.logger.exception",
        ) as log_exception,
    ):
        _run_agent_lifecycle_iteration()

    sync_alerts.assert_called_once_with(
        alert_db.__enter__.return_value
    )

    log_exception.assert_called_once_with(
        "agent token lifecycle cleanup failed"
    )


def test_alert_monitor_failure_does_not_escape_iteration():
    status_db, alert_db, cleanup_db = _sessions()

    with (
        patch(
            "app.main.SessionLocal",
            side_effect=[
                status_db,
                alert_db,
                cleanup_db,
            ],
        ),
        patch(
            "app.main.evaluate_agent_statuses",
        ),
        patch(
            "app.main.cleanup_expired_pending_rotations",
        ),
        patch(
            "app.main.sync_all_agent_lifecycle_alerts",
            side_effect=RuntimeError("alert monitor failed"),
        ),
        patch(
            "app.main.logger.exception",
        ) as log_exception,
    ):
        _run_agent_lifecycle_iteration()

    log_exception.assert_called_once_with(
        "agent lifecycle alert monitor failed"
    )


def test_lifecycle_iteration_runs_all_operations():
    status_db, alert_db, cleanup_db = _sessions()

    with (
        patch(
            "app.main.SessionLocal",
            side_effect=[
                status_db,
                alert_db,
                cleanup_db,
            ],
        ),
        patch(
            "app.main.evaluate_agent_statuses",
        ) as evaluate_statuses,
        patch(
            "app.main.cleanup_expired_pending_rotations",
        ) as cleanup_rotations,
        patch(
            "app.main.sync_all_agent_lifecycle_alerts",
        ) as sync_alerts,
        patch(
            "app.main.logger.exception",
        ) as log_exception,
    ):
        _run_agent_lifecycle_iteration()

    evaluate_statuses.assert_called_once()
    cleanup_rotations.assert_called_once()
    sync_alerts.assert_called_once()

    log_exception.assert_not_called()


def test_alert_reconciliation_runs_before_token_cleanup():
    status_db, alert_db, cleanup_db = _sessions()
    operations = []

    with (
        patch(
            "app.main.SessionLocal",
            side_effect=[
                status_db,
                alert_db,
                cleanup_db,
            ],
        ),
        patch(
            "app.main.evaluate_agent_statuses",
            side_effect=lambda _db: operations.append(
                "status"
            ),
        ),
        patch(
            "app.main.sync_all_agent_lifecycle_alerts",
            side_effect=lambda _db: operations.append(
                "alerts"
            ),
        ),
        patch(
            "app.main.cleanup_expired_pending_rotations",
            side_effect=lambda _db: operations.append(
                "cleanup"
            ),
        ),
    ):
        _run_agent_lifecycle_iteration()

    assert operations == [
        "status",
        "alerts",
        "cleanup",
    ]
