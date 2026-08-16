from types import SimpleNamespace
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
    from app.db.session import get_db

    monkeypatch.setattr(
        auth_api.settings,
        "auth_rate_limit_enabled",
        True,
    )

    redis = Mock()
    db = Mock()
    audit = Mock()

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
    monkeypatch.setattr(
        auth_api,
        "append_audit",
        audit,
    )

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "blocked@example.com",
                "password": "wrong-password",
            },
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

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

    audit.assert_called_once()

    audit_kwargs = audit.call_args.kwargs

    assert audit_kwargs["action"] == "auth.login"
    assert audit_kwargs["result"] == "denied"
    assert audit_kwargs["details"] == {
        "account_fingerprint": auth_api.account_fingerprint(
            "blocked@example.com"
        ),
        "reason": "rate_limited",
        "stage": "precheck",
    }

    db.commit.assert_called_once()


def test_login_rate_limit_redis_failure_is_503(
    monkeypatch,
):
    from app.db.session import get_db

    monkeypatch.setattr(
        auth_api.settings,
        "auth_rate_limit_enabled",
        True,
    )

    redis = Mock()
    db = Mock()
    audit = Mock()

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
    monkeypatch.setattr(
        auth_api,
        "append_audit",
        audit,
    )

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "wrong-password",
            },
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 503
    assert response.json() == {
        "detail": "authentication_service_unavailable"
    }

    audit.assert_called_once()

    audit_kwargs = audit.call_args.kwargs

    assert audit_kwargs["action"] == "auth.login"
    assert audit_kwargs["result"] == "error"
    assert audit_kwargs["details"] == {
        "account_fingerprint": auth_api.account_fingerprint(
            "user@example.com"
        ),
        "reason": "rate_limit_unavailable",
        "stage": "precheck",
    }

    db.commit.assert_called_once()


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



def test_successful_login_clears_only_account_rate_limit(
    monkeypatch,
):
    from app.db.session import get_db
    from app.schemas.auth import TokenResponse

    monkeypatch.setattr(
        auth_api.settings,
        "auth_rate_limit_enabled",
        True,
    )

    redis = Mock()
    db = Mock()
    audit = Mock()
    clear_account = Mock()

    user = SimpleNamespace(
        id="user-1",
        password_hash="hashed-password",
        last_login_at=None,
    )

    db.scalar.return_value = user

    monkeypatch.setattr(
        auth_api,
        "_auth_rate_limit_redis",
        lambda: redis,
    )
    monkeypatch.setattr(
        auth_api,
        "login_rate_limit_exceeded",
        lambda *args, **kwargs: False,
    )
    monkeypatch.setattr(
        auth_api,
        "verify_password",
        lambda *args, **kwargs: True,
    )
    monkeypatch.setattr(
        auth_api,
        "clear_account_login_failures",
        clear_account,
    )
    monkeypatch.setattr(
        auth_api,
        "_issue_session",
        lambda *args, **kwargs: TokenResponse(
            access_token="access-token",
            refresh_token="refresh-token",
            expires_in=900,
        ),
    )
    monkeypatch.setattr(
        auth_api,
        "append_audit",
        audit,
    )

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "User@example.com",
                "password": "correct-password",
            },
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200

    clear_account.assert_called_once_with(
        redis,
        email="user@example.com",
    )

    assert "source_ip" not in clear_account.call_args.kwargs

    audit.assert_called_once()
    db.commit.assert_called_once()


def test_failed_login_redis_record_failure_is_audited(
    monkeypatch,
):
    from app.db.session import get_db

    monkeypatch.setattr(
        auth_api.settings,
        "auth_rate_limit_enabled",
        True,
    )

    redis = Mock()
    db = Mock()
    audit = Mock()

    db.scalar.return_value = None

    monkeypatch.setattr(
        auth_api,
        "_auth_rate_limit_redis",
        lambda: redis,
    )
    monkeypatch.setattr(
        auth_api,
        "login_rate_limit_exceeded",
        lambda *args, **kwargs: False,
    )

    def fail_record(*args, **kwargs):
        raise RedisError("redis unavailable")

    monkeypatch.setattr(
        auth_api,
        "record_failed_login",
        fail_record,
    )
    monkeypatch.setattr(
        auth_api,
        "append_audit",
        audit,
    )

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

    assert response.status_code == 503
    assert response.json() == {
        "detail": "authentication_service_unavailable"
    }

    audit.assert_called_once()

    kwargs = audit.call_args.kwargs

    assert kwargs["action"] == "auth.login"
    assert kwargs["result"] == "error"
    assert kwargs["details"] == {
        "account_fingerprint": auth_api.account_fingerprint(
            "missing@example.com"
        ),
        "reason": "rate_limit_unavailable",
        "stage": "record_failure",
    }

    db.commit.assert_called_once()


def test_successful_login_clear_account_redis_failure_is_audited(
    monkeypatch,
):
    from app.db.session import get_db

    monkeypatch.setattr(
        auth_api.settings,
        "auth_rate_limit_enabled",
        True,
    )

    redis = Mock()
    db = Mock()
    audit = Mock()

    user = SimpleNamespace(
        id="user-1",
        password_hash="hashed-password",
        last_login_at=None,
    )

    db.scalar.return_value = user

    monkeypatch.setattr(
        auth_api,
        "_auth_rate_limit_redis",
        lambda: redis,
    )
    monkeypatch.setattr(
        auth_api,
        "login_rate_limit_exceeded",
        lambda *args, **kwargs: False,
    )
    monkeypatch.setattr(
        auth_api,
        "verify_password",
        lambda *args, **kwargs: True,
    )

    def fail_clear(*args, **kwargs):
        raise RedisError("redis unavailable")

    monkeypatch.setattr(
        auth_api,
        "clear_account_login_failures",
        fail_clear,
    )
    monkeypatch.setattr(
        auth_api,
        "append_audit",
        audit,
    )

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "correct-password",
            },
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 503
    assert response.json() == {
        "detail": "authentication_service_unavailable"
    }

    audit.assert_called_once()

    kwargs = audit.call_args.kwargs

    assert kwargs["action"] == "auth.login"
    assert kwargs["result"] == "error"
    assert kwargs["details"] == {
        "account_fingerprint": auth_api.account_fingerprint(
            "user@example.com"
        ),
        "reason": "rate_limit_unavailable",
        "stage": "clear_account",
    }

    db.commit.assert_called_once()



def test_rate_limit_audit_does_not_expose_raw_email(
    monkeypatch,
):
    from app.db.session import get_db

    monkeypatch.setattr(
        auth_api.settings,
        "auth_rate_limit_enabled",
        True,
    )

    redis = Mock()
    db = Mock()
    audit = Mock()

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
    monkeypatch.setattr(
        auth_api,
        "append_audit",
        audit,
    )

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "Private.User@example.com",
                "password": "wrong-password",
            },
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 429

    details = audit.call_args.kwargs["details"]

    assert "email" not in details
    assert "Private.User@example.com" not in str(details)
    assert "private.user@example.com" not in str(details)

    assert details["account_fingerprint"] == (
        auth_api.account_fingerprint(
            "private.user@example.com"
        )
    )


def test_invalid_credentials_audit_uses_account_fingerprint(
    monkeypatch,
):
    from app.db.session import get_db

    monkeypatch.setattr(
        auth_api.settings,
        "auth_rate_limit_enabled",
        False,
    )

    db = Mock()
    audit = Mock()

    db.scalar.return_value = None

    monkeypatch.setattr(
        auth_api,
        "append_audit",
        audit,
    )

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "Private.User@example.com",
                "password": "wrong-password",
            },
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 401
    assert response.json() == {
        "detail": "invalid_credentials"
    }

    audit.assert_called_once()

    kwargs = audit.call_args.kwargs
    details = kwargs["details"]

    assert kwargs["action"] == "auth.login"
    assert kwargs["result"] == "denied"

    assert details == {
        "account_fingerprint": auth_api.account_fingerprint(
            "private.user@example.com"
        ),
        "reason": "invalid_credentials",
        "stage": "credentials",
    }

    assert "email" not in details
    assert "Private.User@example.com" not in str(details)
    assert "private.user@example.com" not in str(details)

    db.commit.assert_called_once()
