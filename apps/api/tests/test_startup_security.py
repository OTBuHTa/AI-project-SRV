import pytest

from app.core.config import Settings
from app.core.startup_security import (
    validate_production_security,
)


def _settings(**overrides) -> Settings:
    values = {
        "app_env": "production",
        "jwt_secret": "strong-production-secret",
        "bootstrap_enabled": False,
        "metrics_bearer_token": "metrics-secret",
    }
    values.update(overrides)
    return Settings(**values)


def test_non_production_allows_development_defaults():
    settings = Settings(
        app_env="development",
    )

    validate_production_security(settings)


def test_production_accepts_hardened_configuration():
    validate_production_security(
        _settings()
    )


def test_production_rejects_default_jwt_secret():
    with pytest.raises(
        RuntimeError,
        match="JWT_SECRET",
    ):
        validate_production_security(
            _settings(
                jwt_secret=(
                    "change-me-before-external-access"
                ),
            )
        )


def test_production_rejects_empty_jwt_secret():
    with pytest.raises(
        RuntimeError,
        match="JWT_SECRET",
    ):
        validate_production_security(
            _settings(jwt_secret="")
        )


def test_production_rejects_enabled_bootstrap():
    with pytest.raises(
        RuntimeError,
        match="BOOTSTRAP_ENABLED",
    ):
        validate_production_security(
            _settings(
                bootstrap_enabled=True,
            )
        )


def test_production_requires_metrics_bearer_token():
    with pytest.raises(
        RuntimeError,
        match="METRICS_BEARER_TOKEN",
    ):
        validate_production_security(
            _settings(
                metrics_bearer_token="",
            )
        )


def test_production_reports_all_security_errors():
    with pytest.raises(RuntimeError) as exc_info:
        validate_production_security(
            _settings(
                jwt_secret=(
                    "change-me-before-external-access"
                ),
                bootstrap_enabled=True,
                metrics_bearer_token="",
            )
        )

    message = str(exc_info.value)

    assert "JWT_SECRET" in message
    assert "BOOTSTRAP_ENABLED" in message
    assert "METRICS_BEARER_TOKEN" in message
