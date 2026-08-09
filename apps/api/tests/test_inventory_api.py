from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1.inventory import (
    list_resource_inventory,
    resource_inventory_summary,
)


def test_inventory_read_rejects_foreign_resource():
    workspace = SimpleNamespace(id=uuid4())
    db = MagicMock()
    db.scalar.return_value = None

    with pytest.raises(HTTPException) as exc:
        list_resource_inventory(
            resource_id=uuid4(),
            kind=None,
            lifecycle_status=None,
            context=(workspace, None),
            db=db,
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "resource_not_found"


def test_inventory_read_rejects_invalid_lifecycle():
    workspace = SimpleNamespace(id=uuid4())
    resource_id = uuid4()

    db = MagicMock()
    db.scalar.return_value = SimpleNamespace(
        id=resource_id,
        workspace_id=workspace.id,
    )

    with pytest.raises(HTTPException) as exc:
        list_resource_inventory(
            resource_id=resource_id,
            kind=None,
            lifecycle_status="deleted",
            context=(workspace, None),
            db=db,
        )

    assert exc.value.status_code == 422
    assert exc.value.detail == "invalid_lifecycle_status"


def test_inventory_summary_counts_lifecycle():
    workspace = SimpleNamespace(id=uuid4())
    resource_id = uuid4()

    rows = [
        SimpleNamespace(
            kind="cpu",
            lifecycle_status="observed",
        ),
        SimpleNamespace(
            kind="filesystem",
            lifecycle_status="observed",
        ),
        SimpleNamespace(
            kind="filesystem",
            lifecycle_status="stale",
        ),
        SimpleNamespace(
            kind="docker_container",
            lifecycle_status="absent",
        ),
    ]

    db = MagicMock()
    db.scalar.return_value = SimpleNamespace(
        id=resource_id,
        workspace_id=workspace.id,
    )
    db.scalars.return_value.all.return_value = rows

    result = resource_inventory_summary(
        resource_id=resource_id,
        context=(workspace, None),
        db=db,
    )

    assert result.total_items == 4

    assert result.kinds == {
        "cpu": 1,
        "filesystem": 2,
        "docker_container": 1,
    }

    assert result.lifecycle == {
        "observed": 2,
        "stale": 1,
        "absent": 1,
    }
