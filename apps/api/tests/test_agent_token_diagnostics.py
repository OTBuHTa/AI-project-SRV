import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.api.v1.monitoring import agent_token_lifecycle_diagnostics
from app.services.agent_token_diagnostics import (
    get_agent_token_lifecycle_diagnostics,
)
from app.services.agent_token_lifecycle import (
    AGENT_TOKEN_ROTATION_PREPARE_TTL,
)


def test_agent_token_lifecycle_diagnostics_aggregate():
    now = datetime.now(UTC)
    prepared_at = now - timedelta(minutes=5)
    workspace_id = uuid.uuid4()

    row = SimpleNamespace(
        agents_total=12,
        pending_rotations=3,
        expired_pending_rotations=1,
        incomplete_pending_rotations=1,
        revoked_with_pending_rotation=0,
        oldest_pending_prepared_at=prepared_at,
    )

    db = MagicMock()
    db.execute.return_value.one.return_value = row

    result = get_agent_token_lifecycle_diagnostics(
        db,
        workspace_id,
        now=now,
    )

    assert result == {
        "workspace_id": str(workspace_id),
        "agents_total": 12,
        "pending_rotations": 3,
        "expired_pending_rotations": 1,
        "incomplete_pending_rotations": 1,
        "revoked_with_pending_rotation": 0,
        "oldest_pending_prepared_at": prepared_at.isoformat(),
        "prepare_ttl_seconds": int(
            AGENT_TOKEN_ROTATION_PREPARE_TTL.total_seconds()
        ),
        "observed_at": now.isoformat(),
    }

    assert "token_hash" not in result
    assert "pending_token_hash" not in result
    db.execute.assert_called_once()


def test_monitoring_endpoint_scopes_diagnostics_to_workspace():
    workspace_id = uuid.uuid4()
    workspace = SimpleNamespace(id=workspace_id)
    context = (workspace, SimpleNamespace())
    db = MagicMock()

    expected = {
        "workspace_id": str(workspace_id),
        "agents_total": 4,
        "pending_rotations": 1,
        "expired_pending_rotations": 0,
        "incomplete_pending_rotations": 0,
        "revoked_with_pending_rotation": 0,
        "oldest_pending_prepared_at": None,
        "prepare_ttl_seconds": 900,
        "observed_at": datetime.now(UTC).isoformat(),
    }

    with patch(
        "app.api.v1.monitoring."
        "get_agent_token_lifecycle_diagnostics",
        return_value=expected,
    ) as diagnostics:
        result = agent_token_lifecycle_diagnostics(
            context=context,
            db=db,
        )

    assert result == expected
    diagnostics.assert_called_once_with(
        db,
        workspace_id,
    )
