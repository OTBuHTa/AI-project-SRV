from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from redis.exceptions import RedisError

import app.api.v1.auth as auth_api
from app.main import app


client = TestClient(app)


def test_login_returns_429_when_rate_limit_exceeded(
    monkeypatch,
):
    monkeypatch.setattr(
        auth_api.settings,
        "auth_rate_limit_enabled",
        True,
    )

    redis = Mock()

    monkeypatch.setattr(
        auth_api,
        "_auth_rate_limit_redis",
        lambda: redis,
    )
    monkeypatch.setattr(
        auth_api,
        "login_rate_limit_exceeded",
        lambda *args, **kwargs: True,
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "blocked@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 429
    assert response.json() == {
        "detail": "too_many_login_attempts"
    }
    assert (
        response.headers["retry-after"]
        == str(
            auth_api.settings.auth_rate_limit_window_seconds
        )
    )


def test_login_rate_limit_redis_failure_is_503(
    monkeypatch,
):
    monkeypatch.setattr(
        auth_api.settings,
        "auth_rate_limit_enabled",
        True,
    )

    redis = Mock()

    monkeypatch.setattr(
        auth_api,
        "_auth_rate_limit_redis",
        lambda: redis,
    )

    def fail(*args, **kwargs):
        raise RedisError("redis unavailable")

    monkeypatch.setattr(
        auth_api,
        "login_rate_limit_exceeded",
        fail,
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "user@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "authentication_service_unavailable"
    }


def test_login_rate_limit_disabled_skips_redis(
    monkeypatch,
):
    from app.db.session import get_db

    monkeypatch.setattr(
        auth_api.settings,
        "auth_rate_limit_enabled",
        False,
    )

    def unexpected():
        pytest.fail(
            "Redis must not be used when limiter is disabled"
        )

    monkeypatch.setattr(
        auth_api,
        "_auth_rate_limit_redis",
        unexpected,
    )
    monkeypatch.setattr(
        auth_api,
        "append_audit",
        lambda *args, **kwargs: None,
    )

    db = Mock()
    db.scalar.return_value = None

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "missing@example.com",
                "password": "wrong-password",
            },
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 401
    assert response.json() == {
        "detail": "invalid_credentials"
    }

    db.scalar.assert_called_once()
    db.commit.assert_called_once()
