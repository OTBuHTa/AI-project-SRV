from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.agent_lifecycle_alert_events import (
    sync_agent_lifecycle_alert_events,
)
from app.services.agent_lifecycle_alerts import (
    AgentLifecycleAlert,
)


def _event(code: str):
    return SimpleNamespace(
        code=code,
        severity="warning",
        message="old message",
        active=True,
        first_seen_at=None,
        last_seen_at=None,
        resolved_at=None,
    )


def test_sync_resolves_alerts_that_disappear():
    now = datetime.now(UTC)

    active = _event("agent_token_rotation_expired")

    db = MagicMock()
    db.scalars.return_value.all.return_value = [active]

    result = sync_agent_lifecycle_alert_events(
        db,
        workspace_id="workspace-1",
        alerts=[],
        now=now,
    )

    assert result == []
    assert active.active is False
    assert active.resolved_at == now
    assert active.last_seen_at == now
    db.commit.assert_called_once()


def test_sync_keeps_current_active_alert():
    now = datetime.now(UTC)

    active = _event("agent_token_rotation_expired")

    db = MagicMock()
    db.scalars.return_value.all.return_value = [active]

    alert = AgentLifecycleAlert(
        severity="warning",
        code="agent_token_rotation_expired",
        message="1 expired agent token rotation.",
    )

    result = sync_agent_lifecycle_alert_events(
        db,
        workspace_id="workspace-1",
        alerts=[alert],
        now=now,
    )

    assert result == [active]
    assert active.active is True
    assert active.resolved_at is None

    db.execute.assert_called_once()
    db.commit.assert_called_once()


def test_sync_resolves_only_missing_codes():
    now = datetime.now(UTC)

    expired = _event("agent_token_rotation_expired")
    incomplete = _event("agent_token_rotation_incomplete")

    db = MagicMock()
    db.scalars.return_value.all.return_value = [
        expired,
        incomplete,
    ]

    alerts = [
        AgentLifecycleAlert(
            severity="critical",
            code="agent_token_rotation_incomplete",
            message="1 incomplete token rotation.",
        )
    ]

    result = sync_agent_lifecycle_alert_events(
        db,
        workspace_id="workspace-1",
        alerts=alerts,
        now=now,
    )

    assert result == [incomplete]

    assert expired.active is False
    assert expired.resolved_at == now

    assert incomplete.active is True
    assert incomplete.resolved_at is None

    db.commit.assert_called_once()
