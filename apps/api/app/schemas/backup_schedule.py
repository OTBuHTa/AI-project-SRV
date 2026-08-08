from datetime import datetime

from pydantic import BaseModel, Field


class BackupScheduleUpdate(BaseModel):
    enabled: bool = True
    interval_minutes: int = Field(default=1440, ge=15)
    retention_keep_last: int = Field(default=7, ge=1)
    retention_max_age_days: int = Field(default=30, ge=1)


class BackupScheduleOut(BaseModel):
    id: str
    workspace_id: str
    enabled: bool
    interval_minutes: int
    retention_keep_last: int
    retention_max_age_days: int
    last_run_at: datetime | None
    last_success_at: datetime | None
    next_run_at: datetime | None

    model_config = {
        "from_attributes": True,
    }
