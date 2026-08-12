from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.api.v1 import agents as agents_api
from app.db.session import get_db
from app.main import app


def _make_agent():
    agent = MagicMock()
    agent.id = "11111111-1111-1111-1111-111111111111"
    agent.workspace_id = "22222222-2222-2222-2222-222222222222"
    agent.revoked_at = None
    agent.token_expires_at = (
        datetime.now(UTC) + timedelta(days=1)
    )
    agent.token_rotated_at = None
    agent.token_hash = agents_api._hash_token(
        "agent-old-token"
    )
    return agent


def test_self_rotation_replaces_token(monkeypatch):
    agent = _make_agent()

    db = MagicMock()
    db.scalar.return_value = agent

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    monkeypatch.setattr(
        agents_api,
        "_new_token",
        lambda prefix: (
            "agent-new-token",
            agents_api._hash_token(
                "agent-new-token"
            ),
        ),
    )

    try:
        client = TestClient(app)

        response = client.post(
            "/api/v1/agents/token/rotate-self",
            headers={
                "Authorization":
                    "Bearer agent-old-token",
            },
        )

        assert response.status_code == 200

        payload = response.json()

        assert payload["agent_token"] == (
            "agent-new-token"
        )
        assert agent.token_hash == (
            agents_api._hash_token(
                "agent-new-token"
            )
        )
        assert agent.token_rotated_at is not None
        db.commit.assert_called_once()
    finally:
        app.dependency_overrides.clear()


def test_self_rotation_rejects_expired_token():
    agent = _make_agent()
    agent.token_expires_at = (
        datetime.now(UTC) - timedelta(seconds=1)
    )

    db = MagicMock()
    db.scalar.return_value = agent

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    try:
        client = TestClient(app)

        response = client.post(
            "/api/v1/agents/token/rotate-self",
            headers={
                "Authorization":
                    "Bearer agent-old-token",
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == (
            "expired_agent_token"
        )

        db.commit.assert_not_called()
    finally:
        app.dependency_overrides.clear()


def test_self_rotation_rejects_revoked_agent():
    agent = _make_agent()
    agent.revoked_at = datetime.now(UTC)

    db = MagicMock()
    db.scalar.return_value = agent

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    try:
        client = TestClient(app)

        response = client.post(
            "/api/v1/agents/token/rotate-self",
            headers={
                "Authorization":
                    "Bearer agent-old-token",
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == (
            "invalid_agent_token"
        )

        db.commit.assert_not_called()
    finally:
        app.dependency_overrides.clear()
