from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.core import Resource, ResourceInventoryItem


def reconcile_inventory_snapshot(
    db: Session,
    *,
    workspace_id: UUID,
    resource_id: UUID,
    items: list[dict],
    observed_at: datetime | None = None,
) -> list[ResourceInventoryItem]:
    observed_at = observed_at or datetime.now(timezone.utc)

    resource = db.scalar(
        select(Resource).where(
            Resource.id == resource_id,
            Resource.workspace_id == workspace_id,
        )
    )

    if resource is None:
        raise ValueError("resource_not_found")

    identities: list[tuple[str, str]] = []

    for item in items:
        kind = item["kind"]
        external_id = item["external_id"]

        statement = (
            insert(ResourceInventoryItem)
            .values(
                id=uuid4(),
                workspace_id=workspace_id,
                resource_id=resource_id,
                kind=kind,
                external_id=external_id,
                name=item["name"],
                status=item.get("status", "unknown"),
                attributes=item.get("attributes", {}),
                observed_at=observed_at,
                created_at=observed_at,
                updated_at=observed_at,
            )
            .on_conflict_do_update(
                constraint="uq_resource_inventory_identity",
                set_={
                    "workspace_id": workspace_id,
                    "name": item["name"],
                    "status": item.get(
                        "status",
                        "unknown",
                    ),
                    "attributes": item.get(
                        "attributes",
                        {},
                    ),
                    "observed_at": observed_at,
                    "updated_at": observed_at,
                },
            )
        )

        db.execute(statement)
        identities.append((kind, external_id))

    db.commit()

    if not identities:
        return []

    rows = db.scalars(
        select(ResourceInventoryItem)
        .where(
            ResourceInventoryItem.workspace_id
            == workspace_id,
            ResourceInventoryItem.resource_id
            == resource_id,
        )
        .order_by(
            ResourceInventoryItem.kind,
            ResourceInventoryItem.name,
        )
    ).all()

    identity_set = set(identities)

    return [
        row
        for row in rows
        if (row.kind, row.external_id) in identity_set
    ]
