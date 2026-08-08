from unittest.mock import MagicMock, patch

from app.services.backup_scheduler_worker import run_once


@patch("app.services.backup_scheduler_worker.sync_scheduled_workspace_alerts")
@patch("app.services.backup_scheduler_worker.SessionLocal")
@patch("app.services.backup_scheduler_worker.get_due_schedules")
@patch("app.services.backup_scheduler_worker.has_active_backup")
@patch("app.services.backup_scheduler_worker.mark_schedule_started")
@patch("app.services.backup_scheduler_worker.mark_schedule_succeeded")
@patch("app.services.backup_scheduler_worker.create_backup_job")
@patch("app.services.backup_scheduler_worker.execute_backup_job")
def test_run_once_executes_due_backup(
    execute_backup,
    create_job,
    mark_succeeded,
    mark_started,
    has_active,
    get_due,
    session_local,
    sync_alerts,
):
    schedule = MagicMock()
    schedule.workspace_id = "workspace-1"
    schedule.id = "schedule-1"

    job = MagicMock()
    job.id = "job-1"

    get_due.return_value = [schedule]
    has_active.return_value = False
    create_job.return_value = job

    db = MagicMock()
    session_local.return_value.__enter__.return_value = db

    processed = run_once()

    assert processed == 1
    sync_alerts.assert_called_once_with(db)

    has_active.assert_called_once_with(
        db,
        workspace_id="workspace-1",
    )

    mark_started.assert_called_once_with(schedule)

    create_job.assert_called_once_with(
        db,
        workspace_id="workspace-1",
        backup_type="postgres",
    )

    execute_backup.assert_called_once_with(
        db,
        job=job,
    )

    mark_succeeded.assert_called_once_with(schedule)


@patch("app.services.backup_scheduler_worker.sync_scheduled_workspace_alerts")
@patch("app.services.backup_scheduler_worker.SessionLocal")
@patch("app.services.backup_scheduler_worker.get_due_schedules")
@patch("app.services.backup_scheduler_worker.has_active_backup")
@patch("app.services.backup_scheduler_worker.create_backup_job")
@patch("app.services.backup_scheduler_worker.execute_backup_job")
@patch("app.services.backup_scheduler_worker.fail_backup_job")
def test_run_once_marks_failed_backup(
    fail_job,
    execute_backup,
    create_job,
    has_active,
    get_due,
    session_local,
    sync_alerts,
):
    schedule = MagicMock()
    schedule.workspace_id = "workspace-1"
    schedule.interval_minutes = 60

    job = MagicMock()
    job.id = "job-1"

    error = RuntimeError("backup failed")

    get_due.return_value = [schedule]
    has_active.return_value = False
    create_job.return_value = job
    execute_backup.side_effect = error

    db = MagicMock()
    session_local.return_value.__enter__.return_value = db

    processed = run_once()

    assert processed == 1

    fail_job.assert_called_once_with(
        db,
        job=job,
        error=error,
    )


@patch("app.services.backup_scheduler_worker.sync_scheduled_workspace_alerts")
@patch("app.services.backup_scheduler_worker.SessionLocal")
@patch("app.services.backup_scheduler_worker.get_due_schedules")
@patch("app.services.backup_scheduler_worker.has_active_backup")
@patch("app.services.backup_scheduler_worker.create_backup_job")
def test_active_backup_is_skipped(
    create_job,
    has_active,
    get_due,
    session_local,
    sync_alerts,
):
    schedule = MagicMock()
    schedule.workspace_id = "workspace-1"

    get_due.return_value = [schedule]
    has_active.return_value = True

    db = MagicMock()
    session_local.return_value.__enter__.return_value = db

    processed = run_once()

    assert processed == 0
    create_job.assert_not_called()
    sync_alerts.assert_called_once_with(db)


@patch("app.services.backup_scheduler_worker.sync_scheduled_workspace_alerts")
@patch("app.services.backup_scheduler_worker.SessionLocal")
@patch("app.services.backup_scheduler_worker.get_due_schedules")
def test_scheduler_due_query_is_bounded(
    get_due,
    session_local,
    sync_alerts,
):
    db = MagicMock()
    session_local.return_value.__enter__.return_value = db
    get_due.return_value = []

    run_once()

    sync_alerts.assert_called_once_with(db)
    assert get_due.call_count == 1
    assert get_due.call_args.kwargs["limit"] == 10
