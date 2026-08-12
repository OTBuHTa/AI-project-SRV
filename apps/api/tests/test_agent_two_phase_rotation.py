import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.api.v1 import agents as agents_api
from app.db.session import get_db
from app.main import app


OLD_TOKEN = "agent-old-token"
PENDING_TOKEN = "agent-pending-token"


def _make_agent():
    agent = MagicMock()

    agent.id = uuid.UUID(
        "11111111-1111-1111-1111-111111111111"
    )
    agent.workspace_id = uuid.UUID(
        "22222222-2222-2222-2222-222222222222"
    )

    agent.revoked_at = None
    agent.token_hash = agents_api._hash_token(OLD_TOKEN)
    agent.token_expires_at = (
        datetime.now(UTC) + timedelta(days=30)
    )
    agent.token_rotated_at = None

    agent.pending_token_hash = None
    agent.pending_token_expires_at = None
    agent.token_rotation_prepared_at = None

    return agent


def test_prepare_keeps_old_token_active(
    monkeypatch,
):
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
            PENDING_TOKEN,
            agents_api._hash_token(PENDING_TOKEN),
        ),
    )

    try:
        client = TestClient(app)

        old_hash = agent.token_hash

        response = client.post(
            "/api/v1/agents/token/rotate-self/prepare",
            headers={
                "Authorization": f"Bearer {OLD_TOKEN}",
            },
        )

        assert response.status_code == 200
        assert agent.token_hash == old_hash

        assert agent.pending_token_hash == (
            agents_api._hash_token(PENDING_TOKEN)
        )

        assert (
            response.json()["pending_agent_token"]
            == PENDING_TOKEN
        )

        db.commit.assert_called_once()
    finally:
        app.dependency_overrides.clear()


def test_commit_promotes_pending_token():
    agent = _make_agent()

    agent.pending_token_hash = (
        agents_api._hash_token(PENDING_TOKEN)
    )
    agent.pending_token_expires_at = (
        datetime.now(UTC) + timedelta(days=90)
    )
    agent.token_rotation_prepared_at = datetime.now(UTC)

    db = MagicMock()
    db.scalar.return_value = agent

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    try:
        client = TestClient(app)

        response = client.post(
            "/api/v1/agents/token/rotate-self/commit",
            headers={
                "Authorization":
                    f"Bearer {PENDING_TOKEN}",
            },
        )

        assert response.status_code == 200

        assert agent.token_hash == (
            agents_api._hash_token(PENDING_TOKEN)
        )

        assert agent.pending_token_hash is None
        assert agent.pending_token_expires_at is None
        assert agent.token_rotation_prepared_at is None
        assert agent.token_rotated_at is not None

        db.commit.assert_called_once()
    finally:
        app.dependency_overrides.clear()


def test_expired_prepare_keeps_old_token():
    agent = _make_agent()

    old_hash = agent.token_hash

    agent.pending_token_hash = (
        agents_api._hash_token(PENDING_TOKEN)
    )
    agent.pending_token_expires_at = (
        datetime.now(UTC) + timedelta(days=90)
    )
    agent.token_rotation_prepared_at = (
        datetime.now(UTC)
        - agents_api.AGENT_TOKEN_ROTATION_PREPARE_TTL
        - timedelta(seconds=1)
    )

    db = MagicMock()
    db.scalar.return_value = agent

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    try:
        client = TestClient(app)

        response = client.post(
            "/api/v1/agents/token/rotate-self/commit",
            headers={
                "Authorization":
                    f"Bearer {PENDING_TOKEN}",
            },
        )

        assert response.status_code == 401
        assert (
            response.json()["detail"]
            == "rotation_prepare_expired"
        )

        assert agent.token_hash == old_hash
        assert agent.pending_token_hash is None
        assert agent.pending_token_expires_at is None
    finally:
        app.dependency_overrides.clear()


def test_commit_is_idempotent_after_promotion():
    agent = _make_agent()

    agent.token_hash = (
        agents_api._hash_token(PENDING_TOKEN)
    )
    agent.token_rotated_at = datetime.now(UTC)
    agent.token_expires_at = (
        datetime.now(UTC) + timedelta(days=90)
    )

    db = MagicMock()
    db.scalar.side_effect = [
        None,
        agent,
    ]

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    try:
        client = TestClient(app)

        with patch(
            "app.api.v1.agents.append_audit"
        ) as audit:
            response = client.post(
                "/api/v1/agents/token/rotate-self/commit",
                headers={
                    "Authorization":
                        f"Bearer {PENDING_TOKEN}",
                },
            )

        assert response.status_code == 200
        assert response.json()["agent_id"] == str(
            agent.id
        )

        audit.assert_called_once()
        assert (
            audit.call_args.kwargs["action"]
            == "agent.token.rotate.commit.recovered"
        )

        db.commit.assert_called_once()
    finally:
        app.dependency_overrides.clear()


def test_commit_rejects_unknown_pending_token():
    db = MagicMock()
    db.scalar.side_effect = [
        None,
        None,
    ]

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    try:
        client = TestClient(app)

        response = client.post(
            "/api/v1/agents/token/rotate-self/commit",
            headers={
                "Authorization":
                    "Bearer unknown-token",
            },
        )

        assert response.status_code == 401
        assert (
            response.json()["detail"]
            == "invalid_pending_agent_token"
        )
    finally:
        app.dependency_overrides.clear()


def test_expired_prepare_is_audited():
    agent = _make_agent()

    agent.pending_token_hash = (
        agents_api._hash_token(PENDING_TOKEN)
    )
    agent.pending_token_expires_at = (
        datetime.now(UTC) + timedelta(days=90)
    )
    agent.token_rotation_prepared_at = (
        datetime.now(UTC)
        - agents_api.AGENT_TOKEN_ROTATION_PREPARE_TTL
        - timedelta(seconds=1)
    )

    db = MagicMock()
    db.scalar.return_value = agent

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    try:
        client = TestClient(app)

        with patch(
            "app.api.v1.agents.append_audit"
        ) as audit:
            response = client.post(
                "/api/v1/agents/token/rotate-self/commit",
                headers={
                    "Authorization":
                        f"Bearer {PENDING_TOKEN}",
                },
            )

        assert response.status_code == 401
        assert (
            response.json()["detail"]
            == "rotation_prepare_expired"
        )

        audit.assert_called_once()

        kwargs = audit.call_args.kwargs

        assert (
            kwargs["action"]
            == "agent.token.rotate.prepare.expired"
        )
        assert kwargs["actor_id"] == str(agent.id)
        assert kwargs["target_id"] == str(agent.id)

        details = kwargs["details"]

        assert "token_rotation_prepared_at" in details
        assert "expired_at" in details

        assert "pending_token_hash" not in details
        assert "agent_token" not in details

        assert agent.pending_token_hash is None
        assert agent.pending_token_expires_at is None
        assert agent.token_rotation_prepared_at is None

        db.commit.assert_called_once()
    finally:
        app.dependency_overrides.clear()


def test_idempotent_commit_recovery_is_audited():
    agent = _make_agent()

    agent.token_hash = (
        agents_api._hash_token(PENDING_TOKEN)
    )
    agent.token_rotated_at = datetime.now(UTC)
    agent.token_expires_at = (
        datetime.now(UTC) + timedelta(days=90)
    )

    db = MagicMock()
    db.scalar.side_effect = [
        None,
        agent,
    ]

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    try:
        client = TestClient(app)

        with patch(
            "app.api.v1.agents.append_audit"
        ) as audit:
            response = client.post(
                "/api/v1/agents/token/rotate-self/commit",
                headers={
                    "Authorization":
                        f"Bearer {PENDING_TOKEN}",
                },
            )

        assert response.status_code == 200

        audit.assert_called_once()

        kwargs = audit.call_args.kwargs

        assert (
            kwargs["action"]
            == "agent.token.rotate.commit.recovered"
        )
        assert kwargs["actor_id"] == str(agent.id)
        assert kwargs["target_id"] == str(agent.id)

        details = kwargs["details"]

        assert "token_expires_at" in details
        assert "token_rotated_at" in details
        assert "agent_token" not in details
        assert "token_hash" not in details

        db.commit.assert_called_once()
    finally:
        app.dependency_overrides.clear()
