from collections import Counter
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.session import get_db
from app.models.core import Resource, ResourceInventoryItem
from app.schemas.inventory import InventoryItemOut, ResourceInventorySummary

router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])

@router.get("/resources/{resource_id}/items", response_model=list[InventoryItemOut])
def list_resource_inventory(
    resource_id: UUID,
    kind: str | None = Query(default=None),
    lifecycle_status: str | None = Query(default=None),
    context=Depends(require_permission("resource.read")),
    db: Session = Depends(get_db),
):
    workspace, _ = context
    resource = db.scalar(
        select(Resource).where(
            Resource.id == resource_id,
            Resource.workspace_id == workspace.id,
        )
    )
    if resource is None:
        raise HTTPException(status_code=404, detail="resource_not_found")

    query = select(ResourceInventoryItem).where(
        ResourceInventoryItem.workspace_id == workspace.id,
        ResourceInventoryItem.resource_id == resource_id,
    )
    if kind is not None:
        query = query.where(ResourceInventoryItem.kind == kind)

    if lifecycle_status is not None:
        if lifecycle_status not in {
            "observed",
            "stale",
            "absent",
        }:
            raise HTTPException(
                status_code=422,
                detail="invalid_lifecycle_status",
            )

        query = query.where(
            ResourceInventoryItem.lifecycle_status
            == lifecycle_status
        )

    return db.scalars(
        query.order_by(
            ResourceInventoryItem.kind,
            ResourceInventoryItem.name,
        )
    ).all()

@router.get("/resources/{resource_id}/summary", response_model=ResourceInventorySummary)
def resource_inventory_summary(
    resource_id: UUID,
    context=Depends(require_permission("resource.read")),
    db: Session = Depends(get_db),
):
    workspace, _ = context
    resource = db.scalar(
        select(Resource).where(
            Resource.id == resource_id,
            Resource.workspace_id == workspace.id,
        )
    )
    if resource is None:
        raise HTTPException(status_code=404, detail="resource_not_found")

    rows = db.scalars(
        select(ResourceInventoryItem).where(
            ResourceInventoryItem.workspace_id == workspace.id,
            ResourceInventoryItem.resource_id == resource_id,
        )
    ).all()
    kinds = Counter(row.kind for row in rows)
    lifecycle = Counter(
        row.lifecycle_status
        for row in rows
    )

    return ResourceInventorySummary(
        resource_id=resource_id,
        total_items=len(rows),
        kinds=dict(kinds),
        lifecycle=dict(lifecycle),
    )
