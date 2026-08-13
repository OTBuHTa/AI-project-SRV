import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.api.v1.monitoring import (
    list_active_agent_lifecycle_alert_events,
    list_agent_lifecycle_alert_events,
)
from app.schemas.agent_lifecycle_alert_events import (
    AgentLifecycleAlertEventOut,
)


def _event(workspace_id: str):
    now = datetime.now(UTC)

    return SimpleNamespace(
        id=str(uuid.uuid4()),
        workspace_id=workspace_id,
        code="agent_token_rotation_expired",
        severity="warning",
        message="expired rotation",
        active=True,
        first_seen_at=now,
        last_seen_at=now,
        resolved_at=None,
    )


def test_lifecycle_alert_event_schema_from_attributes():
    workspace_id = str(uuid.uuid4())
    event = _event(workspace_id)

    result = AgentLifecycleAlertEventOut.model_validate(
        event
    )

    assert result.id == event.id
    assert result.workspace_id == workspace_id
    assert result.code == event.code
    assert result.active is True


def test_lifecycle_alert_history_is_workspace_scoped():
    workspace_id = uuid.uuid4()
    workspace = SimpleNamespace(id=workspace_id)
    context = (workspace, SimpleNamespace())

    event = _event(str(workspace_id))

    db = MagicMock()
    db.scalars.return_value.all.return_value = [event]

    result = list_agent_lifecycle_alert_events(
        context=context,
        db=db,
    )

    assert result == [event]

    statement = db.scalars.call_args.args[0]
    sql = str(
        statement.compile(
            compile_kwargs={"literal_binds": True}
        )
    ).lower()

    assert str(workspace_id) in sql
    assert "agent_lifecycle_alert_events" in sql
    assert "order by" in sql
    assert "last_seen_at desc" in sql
    assert "limit 200" in sql


def test_active_lifecycle_alerts_are_workspace_scoped():
    workspace_id = uuid.uuid4()
    workspace = SimpleNamespace(id=workspace_id)
    context = (workspace, SimpleNamespace())

    event = _event(str(workspace_id))

    db = MagicMock()
    db.scalars.return_value.all.return_value = [event]

    result = list_active_agent_lifecycle_alert_events(
        context=context,
        db=db,
    )

    assert result == [event]

    statement = db.scalars.call_args.args[0]
    sql = str(
        statement.compile(
            compile_kwargs={"literal_binds": True}
        )
    ).lower()

    assert str(workspace_id) in sql
    assert "agent_lifecycle_alert_events" in sql
    assert "active is true" in sql
    assert "last_seen_at desc" in sql
