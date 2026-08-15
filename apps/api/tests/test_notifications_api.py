from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

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
        endpoint="https://example.com/alerts",
    )

    with patch(
        "app.api.v1.notifications.validate_notification_endpoint"
    ) as validate_endpoint:
        result = create_notification_destination(
            payload,
            context=context("workspace-1"),
            db=db,
        )

    validate_endpoint.assert_called_once()

    assert result.workspace_id == "workspace-1"
    assert result.name == "operations"
    assert result.channel == "webhook"
    assert result.endpoint == "https://example.com/alerts"

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


def test_create_destination_rejects_unsafe_endpoint():
    db = MagicMock()

    payload = NotificationDestinationCreate(
        name="metadata",
        channel="webhook",
        endpoint="http://169.254.169.254/latest/meta-data",
    )

    with pytest.raises(HTTPException) as exc:
        create_notification_destination(
            payload,
            context=context("workspace-1"),
            db=db,
        )

    assert exc.value.status_code == 400
    assert "link-local" in exc.value.detail
    db.add.assert_not_called()


def test_list_deliveries_rejects_invalid_source():
    from app.api.v1.notifications import list_deliveries

    db = MagicMock()

    with pytest.raises(HTTPException) as exc:
        list_deliveries(
            source="unknown",
            delivery_status=None,
            destination_id=None,
            channel=None,
            created_from=None,
            created_to=None,
            offset=0,
            limit=100,
            context=context(),
            db=db,
        )

    assert exc.value.status_code == 400
    assert (
        exc.value.detail
        == "invalid_notification_delivery_source"
    )


def test_list_deliveries_rejects_invalid_status():
    from app.api.v1.notifications import list_deliveries

    db = MagicMock()

    with pytest.raises(HTTPException) as exc:
        list_deliveries(
            source=None,
            delivery_status="unknown",
            destination_id=None,
            channel=None,
            created_from=None,
            created_to=None,
            offset=0,
            limit=100,
            context=context(),
            db=db,
        )

    assert exc.value.status_code == 400
    assert (
        exc.value.detail
        == "invalid_notification_delivery_status"
    )


def test_list_deliveries_uses_current_workspace():
    from app.api.v1.notifications import list_deliveries

    db = MagicMock()

    with patch(
        "app.services.notification_delivery_observability."
        "list_notification_deliveries",
        return_value=[],
    ) as list_service:
        result = list_deliveries(
            source="backup",
            delivery_status="failed",
            destination_id="destination-1",
            channel="webhook",
            created_from=datetime(
                2026, 8, 1, tzinfo=timezone.utc
            ),
            created_to=datetime(
                2026, 8, 15, tzinfo=timezone.utc
            ),
            offset=10,
            limit=25,
            context=context("workspace-1"),
            db=db,
        )

    assert result == []

    list_service.assert_called_once_with(
        db,
        workspace_id="workspace-1",
        source="backup",
        status="failed",
        destination_id="destination-1",
        channel="webhook",
        created_from=datetime(
            2026, 8, 1, tzinfo=timezone.utc
        ),
        created_to=datetime(
            2026, 8, 15, tzinfo=timezone.utc
        ),
        offset=10,
        limit=25,
    )


def test_get_delivery_health_uses_current_workspace():
    from app.api.v1.notifications import get_delivery_health

    db = MagicMock()
    expected = SimpleNamespace(status="healthy")

    with patch(
        "app.services.notification_delivery_observability."
        "get_notification_delivery_health",
        return_value=expected,
    ) as health_service:
        result = get_delivery_health(
            context=context("workspace-1"),
            db=db,
        )

    assert result is expected

    health_service.assert_called_once_with(
        db,
        workspace_id="workspace-1",
    )


def test_list_delivery_problems_rejects_invalid_source():
    from app.api.v1.notifications import (
        list_delivery_problems,
    )

    db = MagicMock()

    with pytest.raises(HTTPException) as exc:
        list_delivery_problems(
            source="unknown",
            problem=None,
            destination_id=None,
            channel=None,
            created_from=None,
            created_to=None,
            offset=0,
            limit=100,
            context=context(),
            db=db,
        )

    assert exc.value.status_code == 400
    assert (
        exc.value.detail
        == "invalid_notification_delivery_source"
    )


def test_list_delivery_problems_uses_current_workspace():
    from app.api.v1.notifications import (
        list_delivery_problems,
    )

    db = MagicMock()

    with patch(
        "app.services.notification_delivery_observability."
        "list_notification_delivery_problems",
        return_value=[],
    ) as problem_service:
        result = list_delivery_problems(
            source="agent_lifecycle",
            problem="retryable_failed",
            destination_id="destination-1",
            channel="webhook",
            created_from=None,
            created_to=None,
            offset=10,
            limit=25,
            context=context("workspace-1"),
            db=db,
        )

    assert result == []

    problem_service.assert_called_once_with(
        db,
        workspace_id="workspace-1",
        source="agent_lifecycle",
        problem="retryable_failed",
        destination_id="destination-1",
        channel="webhook",
        created_from=None,
        created_to=None,
        offset=10,
        limit=25,
    )



def test_list_deliveries_rejects_invalid_time_range():
    from app.api.v1.notifications import list_deliveries

    db = MagicMock()

    with pytest.raises(HTTPException) as exc:
        list_deliveries(
            source=None,
            delivery_status=None,
            destination_id=None,
            channel=None,
            created_from=datetime(
                2026, 8, 15, tzinfo=timezone.utc
            ),
            created_to=datetime(
                2026, 8, 1, tzinfo=timezone.utc
            ),
            offset=0,
            limit=100,
            context=context("workspace-1"),
            db=db,
        )

    assert exc.value.status_code == 400
    assert (
        exc.value.detail
        == "invalid_notification_delivery_time_range"
    )


def test_list_delivery_problems_rejects_invalid_problem():
    from app.api.v1.notifications import (
        list_delivery_problems,
    )

    db = MagicMock()

    with pytest.raises(HTTPException) as exc:
        list_delivery_problems(
            source=None,
            problem="unknown",
            destination_id=None,
            channel=None,
            created_from=None,
            created_to=None,
            offset=0,
            limit=100,
            context=context(),
            db=db,
        )

    assert exc.value.status_code == 400
    assert (
        exc.value.detail
        == "invalid_notification_delivery_problem"
    )


def test_list_delivery_problems_rejects_invalid_time_range():
    from datetime import datetime, timezone

    from app.api.v1.notifications import (
        list_delivery_problems,
    )

    db = MagicMock()

    created_from = datetime(
        2026, 8, 15, 12, 0, tzinfo=timezone.utc
    )
    created_to = datetime(
        2026, 8, 14, 12, 0, tzinfo=timezone.utc
    )

    with pytest.raises(HTTPException) as exc:
        list_delivery_problems(
            source=None,
            problem=None,
            destination_id=None,
            channel=None,
            created_from=created_from,
            created_to=created_to,
            offset=0,
            limit=100,
            context=context(),
            db=db,
        )

    assert exc.value.status_code == 400
    assert (
        exc.value.detail
        == "invalid_notification_delivery_time_range"
    )


def test_get_delivery_count_uses_current_workspace():
    from app.api.v1.notifications import get_delivery_count

    db = MagicMock()

    with patch(
        "app.services.notification_delivery_observability."
        "get_notification_delivery_count",
        return_value=SimpleNamespace(
            total=3,
            backup=2,
            agent_lifecycle=1,
        ),
    ) as count_service:
        result = get_delivery_count(
            source="backup",
            delivery_status="failed",
            destination_id="destination-1",
            channel="webhook",
            created_from=None,
            created_to=None,
            context=context("workspace-1"),
            db=db,
        )

    assert result.total == 3

    count_service.assert_called_once_with(
        db,
        workspace_id="workspace-1",
        source="backup",
        status="failed",
        destination_id="destination-1",
        channel="webhook",
        created_from=None,
        created_to=None,
    )


def test_get_delivery_problem_count_uses_current_workspace():
    from app.api.v1.notifications import (
        get_delivery_problem_count,
    )

    db = MagicMock()

    with patch(
        "app.services.notification_delivery_observability."
        "get_notification_delivery_problem_count",
        return_value=SimpleNamespace(
            total=4,
            backup=1,
            agent_lifecycle=3,
        ),
    ) as count_service:
        result = get_delivery_problem_count(
            source="agent_lifecycle",
            problem="retryable_failed",
            destination_id="destination-1",
            channel="webhook",
            created_from=None,
            created_to=None,
            context=context("workspace-1"),
            db=db,
        )

    assert result.total == 4

    count_service.assert_called_once_with(
        db,
        workspace_id="workspace-1",
        source="agent_lifecycle",
        problem="retryable_failed",
        destination_id="destination-1",
        channel="webhook",
        created_from=None,
        created_to=None,
    )


def test_delivery_time_range_rejects_naive_datetime():
    from datetime import datetime, timezone

    from app.api.v1.notifications import (
        _validate_delivery_time_range,
    )

    created_from = datetime(2026, 8, 15, 12, 0)
    created_to = datetime(
        2026,
        8,
        15,
        13,
        0,
        tzinfo=timezone.utc,
    )

    with pytest.raises(HTTPException) as exc:
        _validate_delivery_time_range(
            created_from,
            created_to,
        )

    assert exc.value.status_code == 400
    assert (
        exc.value.detail
        == "invalid_notification_delivery_timezone"
    )


def test_delivery_time_range_rejects_reverse_range():
    from datetime import datetime, timezone

    from app.api.v1.notifications import (
        _validate_delivery_time_range,
    )

    created_from = datetime(
        2026,
        8,
        15,
        14,
        0,
        tzinfo=timezone.utc,
    )
    created_to = datetime(
        2026,
        8,
        15,
        13,
        0,
        tzinfo=timezone.utc,
    )

    with pytest.raises(HTTPException) as exc:
        _validate_delivery_time_range(
            created_from,
            created_to,
        )

    assert exc.value.status_code == 400
    assert (
        exc.value.detail
        == "invalid_notification_delivery_time_range"
    )
