from datetime import datetime

from pydantic import BaseModel


class BackupStatusOut(BaseModel):
    status: str
    reason: str
    last_verified_at: datetime | None
    verified_age_seconds: int | None
    failed_jobs: int
    last_failure_at: datetime | None
    scheduler_lag_seconds: int
