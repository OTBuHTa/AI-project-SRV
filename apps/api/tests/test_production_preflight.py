import pytest

from app.core.production_preflight import (
    validate_production_env_file,
)


HARDENED_ENV = """
APP_ENV=production
JWT_SECRET=0123456789abcdef0123456789abcdef
BOOTSTRAP_ENABLED=false
METRICS_BEARER_TOKEN=metrics-test-token
SECURE_HEADERS_HSTS_ENABLED=true
AUTH_RATE_LIMIT_ENABLED=true
FORWARDED_ALLOW_IPS=172.30.0.2
"""


def test_preflight_accepts_hardened_file(
    tmp_path,
):
    env_file = tmp_path / ".env.production"
    env_file.write_text(HARDENED_ENV)

    settings = validate_production_env_file(
        env_file,
    )

    assert settings.app_env == "production"
    assert settings.bootstrap_enabled is False


def test_preflight_rejects_development_file(
    tmp_path,
):
    env_file = tmp_path / ".env.production"
    env_file.write_text(
        HARDENED_ENV.replace(
            "APP_ENV=production",
            "APP_ENV=development",
        )
    )

    with pytest.raises(
        RuntimeError,
        match="APP_ENV",
    ):
        validate_production_env_file(
            env_file,
        )


def test_preflight_uses_file_over_ambient_env(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv(
        "APP_ENV",
        "development",
    )
    monkeypatch.setenv(
        "JWT_SECRET",
        "bad",
    )

    env_file = tmp_path / ".env.production"
    env_file.write_text(HARDENED_ENV)

    settings = validate_production_env_file(
        env_file,
    )

    assert settings.app_env == "production"
    assert settings.jwt_secret == (
        "0123456789abcdef"
        "0123456789abcdef"
    )
