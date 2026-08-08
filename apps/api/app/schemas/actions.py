import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class ActionPlanCreate(BaseModel):
    resource_id: uuid.UUID
    capability: str
    parameters: dict
    rationale: str | None = Field(default=None, max_length=2000)

    @field_validator("capability")
    @classmethod
    def capability_allowlist(cls, value: str):
        if value != "docker.container.restart":
            raise ValueError("unsupported_capability")
        return value


class ActionPlanOut(BaseModel):
    id: uuid.UUID
    resource_id: uuid.UUID
    capability: str
    parameters: dict
    rationale: str | None
    risk_level: int
    requires_approval: bool
    status: str
    approved_by_user_id: uuid.UUID | None
    approved_at: datetime | None
    completed_at: datetime | None
    result: dict | None
    source: str
    verification_status: str | None
    verification_result: dict | None
    verification_started_at: datetime | None
    verified_at: datetime | None
    created_at: datetime


class TaskOut(BaseModel):
    task_id: uuid.UUID
    capability: str
    parameters: dict
    lease_seconds: int


class TaskResult(BaseModel):
    status: Literal["success", "failed"]
    exit_code: int | None = None
    stdout: str = Field(default="", max_length=12000)
    stderr: str = Field(default="", max_length=12000)
    duration_ms: int | None = None


# Keep agent result vocabulary intentionally small.
TaskResult.model_rebuild()
