import logging
import time
from datetime import datetime, timezone

from app.db.session import SessionLocal
from app.services.backup_alert_monitor import sync_scheduled_workspace_alerts
from app.services.backup_execution import (
    create_backup_job,
    execute_backup_job,
    fail_backup_job,
)
from app.services.backup_schedule_executor import (
    get_due_schedules,
    has_active_backup,
    mark_schedule_started,
    mark_schedule_succeeded,
)

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 60


def run_once() -> int:
    processed = 0

    with SessionLocal() as db:
        schedules = get_due_schedules(
            db,
            now=datetime.now(timezone.utc),
            limit=10,
        )

        for schedule in schedules:
            workspace_id = str(schedule.workspace_id)

            if has_active_backup(
                db,
                workspace_id=workspace_id,
            ):
                logger.info(
                    "backup already active workspace=%s",
                    workspace_id,
                )
                continue

            mark_schedule_started(schedule)
            db.commit()

            job = create_backup_job(
                db,
                workspace_id=workspace_id,
                backup_type="postgres",
            )

            try:
                execute_backup_job(
                    db,
                    job=job,
                )

                mark_schedule_succeeded(schedule)
                db.commit()

                logger.info(
                    "scheduled backup completed workspace=%s job=%s",
                    workspace_id,
                    job.id,
                )

            except Exception as exc:
                fail_backup_job(
                    db,
                    job=job,
                    error=exc,
                )

                logger.exception(
                    "scheduled backup failed workspace=%s job=%s",
                    workspace_id,
                    job.id,
                )

            processed += 1

        sync_scheduled_workspace_alerts(db)

    return processed


def run_forever() -> None:
    logger.info("backup scheduler worker started")

    while True:
        try:
            run_once()
        except Exception:
            logger.exception("backup scheduler iteration failed")

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_forever()
