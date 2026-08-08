from app.services.backup_alerts import evaluate_backup_alerts
from app.services.backup_status import BackupStatus


def build_backup_protection_summary(
    status: BackupStatus,
) -> dict:
    alerts = evaluate_backup_alerts(status)

    return {
        "status": status.status,
        "reason": status.reason,
        "protected": (
            status.status == "healthy"
            and status.last_verified_at is not None
        ),
        "last_verified_at": status.last_verified_at,
        "failed_jobs": status.failed_jobs,
        "scheduler_lag_seconds": status.scheduler_lag_seconds,
        "alerts": alerts,
    }
