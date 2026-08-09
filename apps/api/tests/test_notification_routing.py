from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.notification_routing import (
    find_matching_destinations,
)


def test_find_matching_destinations_returns_query_results():
    db = MagicMock()

    destination_1 = SimpleNamespace(
        id="destination-1",
        channel="webhook",
    )

    destination_2 = SimpleNamespace(
        id="destination-2",
        channel="webhook",
    )

    db.scalars.return_value.all.return_value = [
        destination_1,
        destination_2,
    ]

    event = SimpleNamespace(
        workspace_id="workspace-1",
        code="backup_missing",
        severity="critical",
    )

    result = find_matching_destinations(
        db,
        event=event,
    )

    assert result == [
        destination_1,
        destination_2,
    ]

    db.scalars.assert_called_once()
