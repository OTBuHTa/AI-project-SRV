from dataclasses import dataclass

from app.services.backup_status import BackupStatus


@dataclass(frozen=True)
class BackupAlert:
    severity: str
    code: str
    message: str


def evaluate_backup_alerts(
    status: BackupStatus,
) -> list[BackupAlert]:
    alerts: list[BackupAlert] = []

    if status.last_verified_at is None:
        alerts.append(
            BackupAlert(
                severity="critical",
                code="backup_missing",
                message="No restore-verified backup is available.",
            )
        )

    if status.verified_age_seconds is not None:
        if status.verified_age_seconds > 24 * 3600:
            alerts.append(
                BackupAlert(
                    severity="warning",
                    code="backup_stale",
                    message="Latest restore-verified backup is older than 24 hours.",
                )
            )

    if status.scheduler_lag_seconds > 10 * 60:
        alerts.append(
            BackupAlert(
                severity="warning",
                code="scheduler_lag",
                message="Backup scheduler is more than 10 minutes behind.",
            )
        )

    if status.failed_jobs > 0:
        alerts.append(
            BackupAlert(
                severity="warning",
                code="recent_failures",
                message=(
                    f"{status.failed_jobs} backup failure(s) "
                    "detected in the recent failure window."
                ),
            )
        )

    return alerts
