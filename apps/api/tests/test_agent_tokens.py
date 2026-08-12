from app.api.v1.agents import _hash_token, _new_token


def test_agent_tokens_are_random_and_hashed():
    first, first_hash = _new_token("agent")
    second, second_hash = _new_token("agent")
    assert first.startswith("agent_")
    assert first != second
    assert first_hash != first
    assert first_hash != second_hash
    assert _hash_token(first) == first_hash


from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.api.v1.agents import _authenticate_agent


def test_expired_agent_token_is_rejected():
    db = MagicMock()

    agent = SimpleNamespace(
        revoked_at=None,
        token_expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    db.scalar.return_value = agent

    with pytest.raises(HTTPException) as exc:
        _authenticate_agent(
            authorization="Bearer agent_test_token",
            db=db,
        )

    assert exc.value.status_code == 401
    assert exc.value.detail == "expired_agent_token"
