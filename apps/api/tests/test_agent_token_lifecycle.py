from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.agent_token_lifecycle import (
    AGENT_TOKEN_ROTATION_PREPARE_TTL,
    cleanup_expired_pending_rotations,
)


def _agent(*, prepared_at):
    return SimpleNamespace(
        id="11111111-1111-1111-1111-111111111111",
        workspace_id="22222222-2222-2222-2222-222222222222",
        pending_token_hash="pending-hash",
        pending_token_expires_at=(
            datetime.now(UTC) + timedelta(days=90)
        ),
        token_rotation_prepared_at=prepared_at,
    )


def test_cleanup_expired_pending_rotation():
    now = datetime.now(UTC)

    agent = _agent(
        prepared_at=(
            now
            - AGENT_TOKEN_ROTATION_PREPARE_TTL
            - timedelta(seconds=1)
        )
    )

    db = MagicMock()
    db.scalars.return_value.all.return_value = [agent]

    with patch(
        "app.services.agent_token_lifecycle.append_audit"
    ) as audit:
        cleaned = cleanup_expired_pending_rotations(
            db,
            now=now,
        )

    assert cleaned == 1

    assert agent.pending_token_hash is None
    assert agent.pending_token_expires_at is None
    assert agent.token_rotation_prepared_at is None

    audit.assert_called_once()

    kwargs = audit.call_args.kwargs

    assert (
        kwargs["action"]
        == "agent.token.rotate.prepare.cleanup"
    )

    details = kwargs["details"]

    assert details["reason"] == "prepare_window_expired"
    assert "cleaned_at" in details
    assert "token_rotation_prepared_at" in details

    assert "pending_token_hash" not in details
    assert "agent_token" not in details

    db.commit.assert_called_once()


def test_cleanup_does_not_commit_when_nothing_expired():
    db = MagicMock()
    db.scalars.return_value.all.return_value = []

    with patch(
        "app.services.agent_token_lifecycle.append_audit"
    ) as audit:
        cleaned = cleanup_expired_pending_rotations(db)

    assert cleaned == 0

    audit.assert_not_called()
    db.commit.assert_not_called()
