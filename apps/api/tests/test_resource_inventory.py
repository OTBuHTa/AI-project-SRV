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
        observed_at=now,
        last_seen_at=now,
        lifecycle_status="observed",
        updated_at=now,
    )

    filesystem = SimpleNamespace(
        kind="filesystem",
        external_id="/",
        name="/",
        observed_at=now,
        last_seen_at=now,
        lifecycle_status="observed",
        updated_at=now,
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


def test_inventory_lifecycle_transitions():
    from datetime import timedelta

    from app.services.resource_inventory import (
        evaluate_inventory_lifecycle,
    )

    workspace_id = uuid4()
    resource_id = uuid4()

    now = datetime(
        2026,
        8,
        9,
        12,
        0,
        tzinfo=timezone.utc,
    )

    resource = SimpleNamespace(
        id=resource_id,
        workspace_id=workspace_id,
    )

    observed = SimpleNamespace(
        last_seen_at=now - timedelta(seconds=60),
        observed_at=now - timedelta(seconds=60),
        lifecycle_status="observed",
        updated_at=None,
    )

    stale = SimpleNamespace(
        last_seen_at=now - timedelta(seconds=600),
        observed_at=now - timedelta(seconds=600),
        lifecycle_status="observed",
        updated_at=None,
    )

    absent = SimpleNamespace(
        last_seen_at=now - timedelta(seconds=3600),
        observed_at=now - timedelta(seconds=3600),
        lifecycle_status="observed",
        updated_at=None,
    )

    db = MagicMock()
    db.scalar.return_value = resource
    db.scalars.return_value.all.return_value = [
        observed,
        stale,
        absent,
    ]

    result = evaluate_inventory_lifecycle(
        db,
        workspace_id=workspace_id,
        resource_id=resource_id,
        now=now,
        stale_after_seconds=300,
        absent_after_seconds=1800,
    )

    assert observed.lifecycle_status == "observed"
    assert stale.lifecycle_status == "stale"
    assert absent.lifecycle_status == "absent"

    assert result == {
        "observed": 1,
        "stale": 1,
        "absent": 1,
    }

    db.commit.assert_called_once()


def test_inventory_lifecycle_rejects_invalid_thresholds():
    from app.services.resource_inventory import (
        evaluate_inventory_lifecycle,
    )

    db = MagicMock()

    with pytest.raises(
        ValueError,
        match="invalid_stale_threshold",
    ):
        evaluate_inventory_lifecycle(
            db,
            workspace_id=uuid4(),
            resource_id=uuid4(),
            stale_after_seconds=0,
            absent_after_seconds=1800,
        )

    with pytest.raises(
        ValueError,
        match="invalid_absent_threshold",
    ):
        evaluate_inventory_lifecycle(
            db,
            workspace_id=uuid4(),
            resource_id=uuid4(),
            stale_after_seconds=300,
            absent_after_seconds=300,
        )
