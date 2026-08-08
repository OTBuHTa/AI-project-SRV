from datetime import datetime

from pydantic import BaseModel


class BackupAlertEventOut(BaseModel):
    id: str
    workspace_id: str
    code: str
    severity: str
    message: str
    active: bool
    first_seen_at: datetime
    last_seen_at: datetime
    resolved_at: datetime | None
    acknowledged_at: datetime | None
    acknowledged_by: str | None

    model_config = {
        "from_attributes": True,
    }
