import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class AIActionProposalRequest(BaseModel):
    resource_id: uuid.UUID
    message: str = Field(min_length=3, max_length=2000)
    container: str | None = Field(default=None, max_length=128)


class AIActionProposalResponse(BaseModel):
    action_plan_id: uuid.UUID
    resource_id: uuid.UUID
    capability: str
    parameters: dict
    rationale: str
    risk_level: int
    requires_approval: bool
    status: str
    source: str
    created_at: datetime
