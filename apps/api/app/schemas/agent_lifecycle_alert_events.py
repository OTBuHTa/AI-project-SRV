from datetime import datetime

from pydantic import BaseModel


class AgentLifecycleAlertEventOut(BaseModel):
    id: str
    workspace_id: str
    code: str
    severity: str
    message: str
    active: bool
    first_seen_at: datetime
    last_seen_at: datetime
    resolved_at: datetime | None

    model_config = {
        "from_attributes": True,
    }
