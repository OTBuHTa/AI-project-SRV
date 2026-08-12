from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1.agents import (
    _hash_token,
    revoke_agent,
    rotate_agent_token,
)


def _request():
    request = MagicMock()
    request.state.request_id = "request-test"
    return request


def _workspace():
    return SimpleNamespace(
        id=uuid4(),
        organization_id=uuid4(),
    )


def _user():
    return SimpleNamespace(id=uuid4())


def test_rotate_agent_is_workspace_scoped():
    workspace = _workspace()
    db = MagicMock()
    db.scalar.return_value = None

    with pytest.raises(HTTPException) as exc:
        rotate_agent_token(
            agent_id=uuid4(),
            request=_request(),
            context=(workspace, None),
            user=_user(),
            db=db,
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "agent_not_found"


def test_revoked_agent_cannot_rotate_token():
    workspace = _workspace()

    agent = SimpleNamespace(
        id=uuid4(),
        workspace_id=workspace.id,
        revoked_at=datetime.now(UTC),
    )

    db = MagicMock()
    db.scalar.return_value = agent

    with pytest.raises(HTTPException) as exc:
        rotate_agent_token(
            agent_id=agent.id,
            request=_request(),
            context=(workspace, None),
            user=_user(),
            db=db,
        )

    assert exc.value.status_code == 409
    assert exc.value.detail == "agent_revoked"


def test_rotate_replaces_token_and_sets_expiry():
    workspace = _workspace()
    old_hash = _hash_token("agent_old")

    agent = SimpleNamespace(
        id=uuid4(),
        workspace_id=workspace.id,
        resource_id=uuid4(),
        token_hash=old_hash,
        token_expires_at=datetime.now(UTC) + timedelta(days=1),
        token_rotated_at=None,
        pending_token_hash=None,
        pending_token_expires_at=None,
        token_rotation_prepared_at=None,
        revoked_at=None,
    )

    db = MagicMock()
    db.scalar.return_value = agent

    with patch(
        "app.api.v1.agents.append_audit"
    ) as audit:
        result = rotate_agent_token(
            agent_id=agent.id,
            request=_request(),
            context=(workspace, None),
            user=_user(),
            db=db,
        )

    assert result.agent_token.startswith("agent_")
    assert agent.token_hash == _hash_token(result.agent_token)
    assert agent.token_hash != old_hash
    assert agent.token_rotated_at is not None
    assert agent.token_expires_at > agent.token_rotated_at
    assert result.agent_token_expires_at == agent.token_expires_at

    audit.assert_called_once()
    details = audit.call_args.kwargs["details"]
    assert "agent_token" not in details
    assert "token_hash" not in details

    db.commit.assert_called_once()


def test_revoke_agent_is_workspace_scoped():
    workspace = _workspace()
    db = MagicMock()
    db.scalar.return_value = None

    with pytest.raises(HTTPException) as exc:
        revoke_agent(
            agent_id=uuid4(),
            request=_request(),
            context=(workspace, None),
            user=_user(),
            db=db,
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "agent_not_found"


def test_revoke_marks_agent_and_resource_offline():
    workspace = _workspace()

    agent = SimpleNamespace(
        id=uuid4(),
        workspace_id=workspace.id,
        resource_id=uuid4(),
        pending_token_hash=None,
        pending_token_expires_at=None,
        token_rotation_prepared_at=None,
        revoked_at=None,
        status="online",
    )
    resource = SimpleNamespace(status="online")

    db = MagicMock()
    db.scalar.return_value = agent
    db.get.return_value = resource

    with patch(
        "app.api.v1.agents.append_audit"
    ) as audit:
        result = revoke_agent(
            agent_id=agent.id,
            request=_request(),
            context=(workspace, None),
            user=_user(),
            db=db,
        )

    assert agent.revoked_at is not None
    assert agent.status == "revoked"
    assert resource.status == "offline"
    assert result.agent_id == agent.id
    assert result.revoked_at == agent.revoked_at

    audit.assert_called_once()
    db.commit.assert_called_once()


def test_revoke_is_idempotent():
    workspace = _workspace()
    revoked_at = datetime.now(UTC)

    agent = SimpleNamespace(
        id=uuid4(),
        workspace_id=workspace.id,
        resource_id=uuid4(),
        revoked_at=revoked_at,
        status="revoked",
    )

    db = MagicMock()
    db.scalar.return_value = agent

    with patch(
        "app.api.v1.agents.append_audit"
    ) as audit:
        result = revoke_agent(
            agent_id=agent.id,
            request=_request(),
            context=(workspace, None),
            user=_user(),
            db=db,
        )

    assert result.revoked_at == revoked_at
    audit.assert_not_called()
    db.commit.assert_not_called()


def test_admin_rotate_invalidates_pending_rotation():
    workspace = _workspace()

    agent = SimpleNamespace(
        id=uuid4(),
        workspace_id=workspace.id,
        resource_id=uuid4(),
        token_hash=_hash_token("agent_old"),
        token_expires_at=datetime.now(UTC) + timedelta(days=1),
        token_rotated_at=None,
        pending_token_hash=_hash_token("agent_pending"),
        pending_token_expires_at=datetime.now(UTC) + timedelta(days=90),
        token_rotation_prepared_at=datetime.now(UTC),
        revoked_at=None,
    )

    db = MagicMock()
    db.scalar.return_value = agent

    with patch(
        "app.api.v1.agents.append_audit"
    ) as audit:
        rotate_agent_token(
            agent_id=agent.id,
            request=_request(),
            context=(workspace, None),
            user=_user(),
            db=db,
        )

    assert agent.pending_token_hash is None
    assert agent.pending_token_expires_at is None
    assert agent.token_rotation_prepared_at is None

    details = audit.call_args.kwargs["details"]
    assert details["pending_rotation_invalidated"] is True

    db.commit.assert_called_once()


def test_revoke_invalidates_pending_rotation():
    workspace = _workspace()

    agent = SimpleNamespace(
        id=uuid4(),
        workspace_id=workspace.id,
        resource_id=uuid4(),
        pending_token_hash=_hash_token("agent_pending"),
        pending_token_expires_at=datetime.now(UTC) + timedelta(days=90),
        token_rotation_prepared_at=datetime.now(UTC),
        revoked_at=None,
        status="online",
    )

    resource = SimpleNamespace(status="online")

    db = MagicMock()
    db.scalar.return_value = agent
    db.get.return_value = resource

    with patch(
        "app.api.v1.agents.append_audit"
    ) as audit:
        revoke_agent(
            agent_id=agent.id,
            request=_request(),
            context=(workspace, None),
            user=_user(),
            db=db,
        )

    assert agent.pending_token_hash is None
    assert agent.pending_token_expires_at is None
    assert agent.token_rotation_prepared_at is None

    assert agent.status == "revoked"
    assert resource.status == "offline"

    details = audit.call_args.kwargs["details"]
    assert details["pending_rotation_invalidated"] is True

    db.commit.assert_called_once()
