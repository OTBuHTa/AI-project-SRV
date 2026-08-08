from datetime import datetime

from pydantic import BaseModel


class BackupAlertOut(BaseModel):
    severity: str
    code: str
    message: str


class BackupAlertsOut(BaseModel):
    status: str
    generated_at: datetime
    alerts: list[BackupAlertOut]
