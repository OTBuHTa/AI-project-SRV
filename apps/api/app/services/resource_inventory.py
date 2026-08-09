from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.core import Resource, ResourceInventoryItem


def _validate_thresholds(
    *,
    stale_after_seconds: int,
    absent_after_seconds: int,
) -> None:
    if stale_after_seconds < 1:
        raise ValueError("invalid_stale_threshold")
    if absent_after_seconds <= stale_after_seconds:
        raise ValueError("invalid_absent_threshold")


def _classify_inventory_rows(
    rows: list[ResourceInventoryItem],
    *,
    now: datetime,
    stale_after_seconds: int,
    absent_after_seconds: int,
) -> dict[str, int]:
    stale_before = now - timedelta(seconds=stale_after_seconds)
    absent_before = now - timedelta(seconds=absent_after_seconds)

    counts = {
        "observed": 0,
        "stale": 0,
        "absent": 0,
    }

    for row in rows:
        last_seen_at = row.last_seen_at or row.observed_at

        if last_seen_at <= absent_before:
            row.lifecycle_status = "absent"
        elif last_seen_at <= stale_before:
            row.lifecycle_status = "stale"
        else:
            row.lifecycle_status = "observed"

        row.updated_at = now
        counts[row.lifecycle_status] += 1

    return counts


def reconcile_inventory_snapshot(
    db: Session,
    *,
    workspace_id: UUID,
    resource_id: UUID,
    items: list[dict],
    observed_at: datetime | None = None,
    stale_after_seconds: int = 300,
    absent_after_seconds: int = 1800,
) -> list[ResourceInventoryItem]:
    observed_at = observed_at or datetime.now(timezone.utc)

    _validate_thresholds(
        stale_after_seconds=stale_after_seconds,
        absent_after_seconds=absent_after_seconds,
    )

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
                last_seen_at=observed_at,
                lifecycle_status="observed",
                created_at=observed_at,
                updated_at=observed_at,
            )
            .on_conflict_do_update(
                constraint="uq_resource_inventory_identity",
                set_={
                    "workspace_id": workspace_id,
                    "name": item["name"],
                    "status": item.get("status", "unknown"),
                    "attributes": item.get("attributes", {}),
                    "observed_at": observed_at,
                    "last_seen_at": observed_at,
                    "lifecycle_status": "observed",
                    "updated_at": observed_at,
                },
            )
        )

        db.execute(statement)
        identities.append((kind, external_id))

    db.flush()

    rows = db.scalars(
        select(ResourceInventoryItem)
        .where(
            ResourceInventoryItem.workspace_id == workspace_id,
            ResourceInventoryItem.resource_id == resource_id,
        )
        .order_by(
            ResourceInventoryItem.kind,
            ResourceInventoryItem.name,
        )
    ).all()

    _classify_inventory_rows(
        rows,
        now=observed_at,
        stale_after_seconds=stale_after_seconds,
        absent_after_seconds=absent_after_seconds,
    )

    db.commit()

    identity_set = set(identities)

    return [
        row
        for row in rows
        if (row.kind, row.external_id) in identity_set
    ]


def evaluate_inventory_lifecycle(
    db: Session,
    *,
    workspace_id: UUID,
    resource_id: UUID,
    now: datetime | None = None,
    stale_after_seconds: int = 300,
    absent_after_seconds: int = 1800,
) -> dict[str, int]:
    now = now or datetime.now(timezone.utc)

    _validate_thresholds(
        stale_after_seconds=stale_after_seconds,
        absent_after_seconds=absent_after_seconds,
    )

    resource = db.scalar(
        select(Resource).where(
            Resource.id == resource_id,
            Resource.workspace_id == workspace_id,
        )
    )

    if resource is None:
        raise ValueError("resource_not_found")

    rows = db.scalars(
        select(ResourceInventoryItem).where(
            ResourceInventoryItem.workspace_id == workspace_id,
            ResourceInventoryItem.resource_id == resource_id,
        )
    ).all()

    counts = _classify_inventory_rows(
        rows,
        now=now,
        stale_after_seconds=stale_after_seconds,
        absent_after_seconds=absent_after_seconds,
    )

    db.commit()

    return counts
