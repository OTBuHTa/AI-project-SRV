from datetime import datetime

from pydantic import BaseModel, Field


class NotificationDestinationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    channel: str = Field(default="webhook", min_length=1, max_length=32)
    endpoint: str = Field(min_length=1)
    enabled: bool = True


class NotificationDestinationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    endpoint: str | None = Field(default=None, min_length=1)
    enabled: bool | None = None


class NotificationDestinationOut(BaseModel):
    id: str
    workspace_id: str
    name: str
    channel: str
    endpoint: str
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class NotificationRouteCreate(BaseModel):
    destination_id: str
    alert_code: str | None = Field(default=None, max_length=64)
    severity: str | None = Field(default=None, max_length=32)
    enabled: bool = True


class NotificationRouteUpdate(BaseModel):
    alert_code: str | None = Field(default=None, max_length=64)
    severity: str | None = Field(default=None, max_length=32)
    enabled: bool | None = None


class NotificationRouteOut(BaseModel):
    id: str
    workspace_id: str
    destination_id: str
    alert_code: str | None
    severity: str | None
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class NotificationDeliveryOut(BaseModel):
    id: str
    source: str
    workspace_id: str
    alert_event_id: str
    channel: str
    destination_id: str | None
    status: str
    attempts: int
    max_attempts: int
    next_attempt_at: datetime | None
    last_attempt_at: datetime | None
    delivered_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime


class NotificationDeliveryHealthCounts(BaseModel):
    total: int
    pending: int
    sending: int
    delivered: int
    failed: int
    canceled: int
    retryable_failed: int
    exhausted_failed: int
    stale_sending: int


class NotificationDeliveryHealthOut(BaseModel):
    status: str
    issues: list[str]
    observed_at: datetime
    claim_timeout_seconds: int
    total: NotificationDeliveryHealthCounts
    backup: NotificationDeliveryHealthCounts
    agent_lifecycle: NotificationDeliveryHealthCounts


class NotificationDeliveryProblemOut(NotificationDeliveryOut):
    problem: str


class NotificationDeliveryCountOut(BaseModel):
    total: int
    backup: int
    agent_lifecycle: int
