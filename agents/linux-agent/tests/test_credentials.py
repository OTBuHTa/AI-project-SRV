from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from ai_srv_agent.credentials import (
    ROTATION_WINDOW,
    rotate_agent_token,
    token_needs_rotation,
)


def test_token_needs_rotation_near_expiry():
    now = datetime.now(UTC)

    state = {
        "agent_token_expires_at": (
            now
            + ROTATION_WINDOW
            - timedelta(seconds=1)
        ).isoformat()
    }

    assert token_needs_rotation(
        state,
        now=now,
    )


def test_token_does_not_need_rotation_when_fresh():
    now = datetime.now(UTC)

    state = {
        "agent_token_expires_at": (
            now
            + ROTATION_WINDOW
            + timedelta(days=1)
        ).isoformat()
    }

    assert not token_needs_rotation(
        state,
        now=now,
    )


def test_missing_expiry_does_not_rotate():
    assert not token_needs_rotation({})


def test_rotate_updates_state_only_after_success(
    monkeypatch,
    tmp_path: Path,
):
    state_file = tmp_path / "agent-state.json"

    state = {
        "api_url": "https://example.test",
        "agent_id": "agent-1",
        "agent_token": "old-token",
        "agent_token_expires_at":
            "2026-08-13T00:00:00+00:00",
    }

    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "agent_id": "agent-1",
        "agent_token": "new-token",
        "agent_token_expires_at":
            "2026-11-10T00:00:00+00:00",
        "token_rotated_at":
            "2026-08-12T00:00:00+00:00",
    }

    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: response,
    )

    assert rotate_agent_token(
        state,
        state_file,
    )

    assert state["agent_token"] == "new-token"
    assert state["agent_token_expires_at"] == (
        "2026-11-10T00:00:00+00:00"
    )

    saved = state_file.read_text()

    assert "new-token" in saved
    assert "old-token" not in saved


def test_failed_rotation_keeps_old_state(
    monkeypatch,
    tmp_path: Path,
):
    state_file = tmp_path / "agent-state.json"

    state = {
        "api_url": "https://example.test",
        "agent_id": "agent-1",
        "agent_token": "old-token",
        "agent_token_expires_at":
            "2026-08-13T00:00:00+00:00",
    }

    def fail(*args, **kwargs):
        request = httpx.Request(
            "POST",
            "https://example.test",
        )

        raise httpx.ConnectError(
            "offline",
            request=request,
        )

    monkeypatch.setattr(
        httpx,
        "post",
        fail,
    )

    with pytest.raises(httpx.ConnectError):
        rotate_agent_token(
            state,
            state_file,
        )

    assert state["agent_token"] == "old-token"
    assert not state_file.exists()
