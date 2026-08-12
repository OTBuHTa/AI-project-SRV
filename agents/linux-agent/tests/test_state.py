import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from ai_srv_agent.state import load_state, save_state


def test_save_state_atomically_replaces_file(tmp_path: Path):
    state_file = tmp_path / "nested" / "agent-state.json"
    state = {
        "api_url": "https://example.test",
        "agent_id": "agent-id",
        "agent_token": "secret",
    }

    save_state(state_file, state)

    assert json.loads(state_file.read_text()) == state
    assert list(state_file.parent.glob("*.tmp")) == []
    if os.name != "nt":
        assert state_file.stat().st_mode & 0o777 == 0o600


def test_save_state_preserves_existing_file_when_replace_fails(tmp_path: Path):
    state_file = tmp_path / "agent-state.json"
    state_file.write_text('{"old": true}')

    with (
        patch("ai_srv_agent.state.os.replace", side_effect=OSError("disk error")),
        pytest.raises(OSError, match="disk error"),
    ):
        save_state(state_file, {"new": True})

    assert json.loads(state_file.read_text()) == {"old": True}
    assert list(tmp_path.glob("*.tmp")) == []


def test_load_state_rejects_missing_credentials(tmp_path: Path):
    state_file = tmp_path / "agent-state.json"
    state_file.write_text('{"api_url": "https://example.test"}')

    with pytest.raises(ValueError, match="agent_id, agent_token"):
        load_state(state_file)
