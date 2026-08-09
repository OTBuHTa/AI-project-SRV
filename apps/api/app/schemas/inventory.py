from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class InventoryItemInput(BaseModel):
    kind: str = Field(min_length=1, max_length=64)
    external_id: str = Field(min_length=1, max_length=255)
    name: str = Field(min_length=1, max_length=255)
    status: str = Field(default="unknown", max_length=32)
    attributes: dict = Field(default_factory=dict)


class InventorySnapshotInput(BaseModel):
    items: list[InventoryItemInput] = Field(
        default_factory=list,
        max_length=4096,
    )


class InventoryItemOut(BaseModel):
    id: UUID
    workspace_id: UUID
    resource_id: UUID
    kind: str
    external_id: str
    name: str
    status: str
    attributes: dict
    observed_at: datetime
    last_seen_at: datetime | None
    lifecycle_status: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class ResourceInventorySummary(BaseModel):
    resource_id: UUID
    total_items: int
    kinds: dict[str, int]
    lifecycle: dict[str, int]
