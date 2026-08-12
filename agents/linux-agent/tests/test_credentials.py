from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

import ai_srv_agent.credentials as credentials
from ai_srv_agent.credentials import (
    ROTATION_WINDOW,
    commit_pending_agent_token_rotation,
    has_pending_agent_token,
    recover_pending_agent_token,
    rotate_agent_token,
    token_needs_rotation,
)


def _state() -> dict:
    return {
        "api_url": "https://example.test",
        "agent_id": "agent-1",
        "agent_token": "old-token",
        "agent_token_expires_at":
            "2026-08-13T00:00:00+00:00",
    }


def _response(payload: dict) -> MagicMock:
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = payload
    return response


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


def test_pending_token_is_detected():
    assert has_pending_agent_token(
        {
            "pending_agent_token":
                "pending-token",
        }
    )

    assert not has_pending_agent_token({})


def test_rotation_persists_pending_before_commit(
    monkeypatch,
    tmp_path: Path,
):
    state_file = tmp_path / "agent-state.json"
    state = _state()

    prepare_response = _response(
        {
            "agent_id": "agent-1",
            "pending_agent_token":
                "pending-token",
            "pending_agent_token_expires_at":
                "2026-11-10T00:00:00+00:00",
            "token_rotation_prepared_at":
                "2026-08-12T00:00:00+00:00",
        }
    )

    commit_response = _response(
        {
            "agent_id": "agent-1",
            "agent_token_expires_at":
                "2026-11-10T00:00:00+00:00",
            "token_rotated_at":
                "2026-08-12T00:00:01+00:00",
        }
    )

    responses = iter(
        [
            prepare_response,
            commit_response,
        ]
    )

    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: next(
            responses
        ),
    )

    monkeypatch.setattr(
        credentials,
        "retry_http",
        lambda operation: operation(),
    )

    snapshots = []
    real_save_state = credentials.save_state

    def record_save(path, value):
        snapshots.append(dict(value))
        real_save_state(path, value)

    monkeypatch.setattr(
        credentials,
        "save_state",
        record_save,
    )

    assert rotate_agent_token(
        state,
        state_file,
    )

    assert len(snapshots) == 2

    assert snapshots[0]["agent_token"] == (
        "old-token"
    )
    assert snapshots[0][
        "pending_agent_token"
    ] == "pending-token"

    assert snapshots[1]["agent_token"] == (
        "pending-token"
    )
    assert (
        "pending_agent_token"
        not in snapshots[1]
    )

    assert state["agent_token"] == (
        "pending-token"
    )

    saved = state_file.read_text()

    assert "pending-token" in saved
    assert "old-token" not in saved


def test_commit_failure_keeps_pending_state(
    monkeypatch,
    tmp_path: Path,
):
    state_file = tmp_path / "agent-state.json"

    state = {
        **_state(),
        "pending_agent_token":
            "pending-token",
        "pending_agent_token_expires_at":
            "2026-11-10T00:00:00+00:00",
        "token_rotation_prepared_at":
            "2026-08-12T00:00:00+00:00",
    }

    credentials.save_state(
        state_file,
        state,
    )

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

    monkeypatch.setattr(
        credentials,
        "retry_http",
        lambda operation: operation(),
    )

    with pytest.raises(httpx.ConnectError):
        commit_pending_agent_token_rotation(
            state,
            state_file,
        )

    assert state["agent_token"] == "old-token"
    assert state["pending_agent_token"] == (
        "pending-token"
    )

    saved = state_file.read_text()

    assert "old-token" in saved
    assert "pending-token" in saved


def test_recovery_promotes_existing_pending_token(
    monkeypatch,
    tmp_path: Path,
):
    state_file = tmp_path / "agent-state.json"

    state = {
        **_state(),
        "pending_agent_token":
            "pending-token",
        "pending_agent_token_expires_at":
            "2026-11-10T00:00:00+00:00",
        "token_rotation_prepared_at":
            "2026-08-12T00:00:00+00:00",
    }

    credentials.save_state(
        state_file,
        state,
    )

    response = _response(
        {
            "agent_id": "agent-1",
            "agent_token_expires_at":
                "2026-11-10T00:00:00+00:00",
            "token_rotated_at":
                "2026-08-12T00:00:01+00:00",
        }
    )

    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: response,
    )

    monkeypatch.setattr(
        credentials,
        "retry_http",
        lambda operation: operation(),
    )

    assert recover_pending_agent_token(
        state,
        state_file,
    )

    assert state["agent_token"] == (
        "pending-token"
    )
    assert (
        "pending_agent_token"
        not in state
    )


def test_prepare_failure_keeps_active_state(
    monkeypatch,
    tmp_path: Path,
):
    state_file = tmp_path / "agent-state.json"
    state = _state()

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

    monkeypatch.setattr(
        credentials,
        "retry_http",
        lambda operation: operation(),
    )

    with pytest.raises(httpx.ConnectError):
        rotate_agent_token(
            state,
            state_file,
        )

    assert state["agent_token"] == "old-token"
    assert (
        "pending_agent_token"
        not in state
    )
    assert not state_file.exists()
