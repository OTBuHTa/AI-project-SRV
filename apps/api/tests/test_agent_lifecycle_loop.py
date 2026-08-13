from unittest.mock import MagicMock, patch

from app.main import _run_agent_lifecycle_iteration


def test_status_failure_does_not_block_token_cleanup():
    status_db = MagicMock()
    cleanup_db = MagicMock()

    with (
        patch(
            "app.main.SessionLocal",
            side_effect=[status_db, cleanup_db],
        ),
        patch(
            "app.main.evaluate_agent_statuses",
            side_effect=RuntimeError("status failed"),
        ) as evaluate_statuses,
        patch(
            "app.main.cleanup_expired_pending_rotations",
        ) as cleanup_rotations,
        patch("app.main.logger.exception") as log_exception,
    ):
        _run_agent_lifecycle_iteration()

    evaluate_statuses.assert_called_once_with(status_db.__enter__.return_value)
    cleanup_rotations.assert_called_once_with(
        cleanup_db.__enter__.return_value
    )
    log_exception.assert_called_once_with(
        "agent status evaluation failed"
    )


def test_token_cleanup_failure_does_not_escape_iteration():
    status_db = MagicMock()
    cleanup_db = MagicMock()

    with (
        patch(
            "app.main.SessionLocal",
            side_effect=[status_db, cleanup_db],
        ),
        patch(
            "app.main.evaluate_agent_statuses",
        ) as evaluate_statuses,
        patch(
            "app.main.cleanup_expired_pending_rotations",
            side_effect=RuntimeError("cleanup failed"),
        ) as cleanup_rotations,
        patch("app.main.logger.exception") as log_exception,
    ):
        _run_agent_lifecycle_iteration()

    evaluate_statuses.assert_called_once_with(status_db.__enter__.return_value)
    cleanup_rotations.assert_called_once_with(
        cleanup_db.__enter__.return_value
    )
    log_exception.assert_called_once_with(
        "agent token lifecycle cleanup failed"
    )


def test_lifecycle_iteration_runs_both_operations():
    status_db = MagicMock()
    cleanup_db = MagicMock()

    with (
        patch(
            "app.main.SessionLocal",
            side_effect=[status_db, cleanup_db],
        ),
        patch(
            "app.main.evaluate_agent_statuses",
        ) as evaluate_statuses,
        patch(
            "app.main.cleanup_expired_pending_rotations",
        ) as cleanup_rotations,
        patch("app.main.logger.exception") as log_exception,
    ):
        _run_agent_lifecycle_iteration()

    evaluate_statuses.assert_called_once_with(status_db.__enter__.return_value)
    cleanup_rotations.assert_called_once_with(
        cleanup_db.__enter__.return_value
    )
    log_exception.assert_not_called()
