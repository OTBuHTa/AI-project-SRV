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
