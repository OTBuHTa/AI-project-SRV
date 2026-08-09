from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.api.v1.notifications import (
    _get_destination,
    _get_route,
    create_notification_destination,
    create_notification_route,
)
from app.schemas.notifications import (
    NotificationDestinationCreate,
    NotificationRouteCreate,
)


def context(workspace_id="workspace-1"):
    return (
        SimpleNamespace(id=workspace_id),
        SimpleNamespace(role="admin"),
    )


def test_get_destination_not_found():
    db = MagicMock()
    db.scalar.return_value = None

    with pytest.raises(HTTPException) as exc:
        _get_destination(
            db,
            workspace_id="workspace-1",
            destination_id="destination-1",
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "notification_destination_not_found"


def test_get_route_not_found():
    db = MagicMock()
    db.scalar.return_value = None

    with pytest.raises(HTTPException) as exc:
        _get_route(
            db,
            workspace_id="workspace-1",
            route_id="route-1",
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "notification_route_not_found"


def test_create_destination_rejects_unknown_channel():
    db = MagicMock()

    payload = NotificationDestinationCreate(
        name="email",
        channel="email",
        endpoint="test@example.invalid",
    )

    with pytest.raises(HTTPException) as exc:
        create_notification_destination(
            payload,
            context=context(),
            db=db,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "unsupported_notification_channel"
    db.add.assert_not_called()


def test_create_destination_uses_current_workspace():
    db = MagicMock()

    payload = NotificationDestinationCreate(
        name="operations",
        channel="webhook",
        endpoint="http://receiver:18080/alerts",
    )

    result = create_notification_destination(
        payload,
        context=context("workspace-1"),
        db=db,
    )

    assert result.workspace_id == "workspace-1"
    assert result.name == "operations"
    assert result.channel == "webhook"
    assert result.endpoint == "http://receiver:18080/alerts"

    db.add.assert_called_once_with(result)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(result)


def test_create_route_rejects_destination_from_other_workspace():
    db = MagicMock()
    db.scalar.return_value = None

    payload = NotificationRouteCreate(
        destination_id="foreign-destination",
        alert_code="backup_missing",
        severity="critical",
    )

    with pytest.raises(HTTPException) as exc:
        create_notification_route(
            payload,
            context=context("workspace-1"),
            db=db,
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "notification_destination_not_found"
    db.add.assert_not_called()


def test_create_route_uses_current_workspace():
    db = MagicMock()

    destination = SimpleNamespace(
        id="destination-1",
        workspace_id="workspace-1",
    )
    db.scalar.return_value = destination

    payload = NotificationRouteCreate(
        destination_id="destination-1",
        alert_code="backup_missing",
        severity="critical",
        enabled=True,
    )

    result = create_notification_route(
        payload,
        context=context("workspace-1"),
        db=db,
    )

    assert result.workspace_id == "workspace-1"
    assert result.destination_id == "destination-1"
    assert result.alert_code == "backup_missing"
    assert result.severity == "critical"

    db.add.assert_called_once_with(result)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(result)
