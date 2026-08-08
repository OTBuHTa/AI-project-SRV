from datetime import datetime

from pydantic import BaseModel

from app.schemas.backup_alerts import BackupAlertOut


class BackupProtectionOut(BaseModel):
    status: str
    reason: str
    protected: bool
    last_verified_at: datetime | None
    failed_jobs: int
    scheduler_lag_seconds: int
    alerts: list[BackupAlertOut]
