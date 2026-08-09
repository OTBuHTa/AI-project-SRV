from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.services.resource_inventory import (
    reconcile_inventory_snapshot,
)


def test_inventory_rejects_foreign_resource():
    db = MagicMock()
    db.scalar.return_value = None

    with pytest.raises(
        ValueError,
        match="resource_not_found",
    ):
        reconcile_inventory_snapshot(
            db,
            workspace_id=uuid4(),
            resource_id=uuid4(),
            items=[],
        )

    db.execute.assert_not_called()


def test_inventory_snapshot_upserts_items():
    workspace_id = uuid4()
    resource_id = uuid4()

    now = datetime(
        2026,
        8,
        9,
        tzinfo=timezone.utc,
    )

    resource = SimpleNamespace(
        id=resource_id,
        workspace_id=workspace_id,
    )

    cpu = SimpleNamespace(
        kind="cpu",
        external_id="cpu",
        name="CPU",
    )

    filesystem = SimpleNamespace(
        kind="filesystem",
        external_id="/",
        name="/",
    )

    db = MagicMock()
    db.scalar.return_value = resource

    db.scalars.return_value.all.return_value = [
        cpu,
        filesystem,
    ]

    result = reconcile_inventory_snapshot(
        db,
        workspace_id=workspace_id,
        resource_id=resource_id,
        observed_at=now,
        items=[
            {
                "kind": "cpu",
                "external_id": "cpu",
                "name": "CPU",
                "status": "online",
                "attributes": {
                    "logical_processors": 24,
                },
            },
            {
                "kind": "filesystem",
                "external_id": "/",
                "name": "/",
                "status": "online",
                "attributes": {
                    "mountpoint": "/",
                },
            },
        ],
    )

    assert result == [
        cpu,
        filesystem,
    ]

    assert db.execute.call_count == 2
    db.commit.assert_called_once()
