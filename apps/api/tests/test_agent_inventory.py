from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1.agents import submit_inventory
from app.schemas.inventory import InventoryItemInput, InventorySnapshotInput


def test_agent_inventory_rejects_identity_mismatch():
    authenticated_agent = SimpleNamespace(
        id=uuid4(),
        workspace_id=uuid4(),
        resource_id=uuid4(),
    )

    with pytest.raises(HTTPException) as exc:
        submit_inventory(
            agent_id=uuid4(),
            payload=InventorySnapshotInput(items=[]),
            authenticated_agent=authenticated_agent,
            db=MagicMock(),
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "agent_identity_mismatch"


def test_agent_inventory_uses_authenticated_scope():
    agent_id = uuid4()
    workspace_id = uuid4()
    resource_id = uuid4()

    authenticated_agent = SimpleNamespace(
        id=agent_id,
        workspace_id=workspace_id,
        resource_id=resource_id,
    )

    payload = InventorySnapshotInput(
        items=[
            InventoryItemInput(
                kind="filesystem",
                external_id="/",
                name="/",
                status="online",
                attributes={
                    "mountpoint": "/",
                    "filesystem": "ext4",
                },
            )
        ]
    )

    expected = [SimpleNamespace(id=uuid4())]

    with patch(
        "app.api.v1.agents.reconcile_inventory_snapshot",
        return_value=expected,
    ) as reconcile:
        result = submit_inventory(
            agent_id=agent_id,
            payload=payload,
            authenticated_agent=authenticated_agent,
            db=MagicMock(),
        )

    assert result == expected
    kwargs = reconcile.call_args.kwargs
    assert kwargs["workspace_id"] == workspace_id
    assert kwargs["resource_id"] == resource_id
    assert kwargs["items"] == [
        {
            "kind": "filesystem",
            "external_id": "/",
            "name": "/",
            "status": "online",
            "attributes": {
                "mountpoint": "/",
                "filesystem": "ext4",
            },
        }
    ]


def test_agent_inventory_missing_resource_returns_404():
    agent_id = uuid4()

    authenticated_agent = SimpleNamespace(
        id=agent_id,
        workspace_id=uuid4(),
        resource_id=uuid4(),
    )

    with patch(
        "app.api.v1.agents.reconcile_inventory_snapshot",
        side_effect=ValueError("resource_not_found"),
    ):
        with pytest.raises(HTTPException) as exc:
            submit_inventory(
                agent_id=agent_id,
                payload=InventorySnapshotInput(items=[]),
                authenticated_agent=authenticated_agent,
                db=MagicMock(),
            )

    assert exc.value.status_code == 404
    assert exc.value.detail == "resource_not_found"
