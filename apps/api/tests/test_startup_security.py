import pytest

from app.core.config import Settings
from app.core.startup_security import (
    validate_production_security,
)


def _settings(**overrides) -> Settings:
    values = {
        "app_env": "production",
        "jwt_secret": (
            "strong-production-secret-"
            "0123456789abcdef"
        ),
        "bootstrap_enabled": False,
        "metrics_bearer_token": "metrics-secret",
        "secure_headers_hsts_enabled": True,
        "auth_rate_limit_enabled": True,
        "forwarded_allow_ips": "172.20.0.10",
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


def test_production_rejects_example_jwt_secret():
    with pytest.raises(
        RuntimeError,
        match="JWT_SECRET",
    ):
        validate_production_security(
            _settings(
                jwt_secret=(
                    "replace-with-at-least-32-random-"
                    "bytes-before-external-access"
                ),
            )
        )


def test_production_rejects_short_jwt_secret():
    with pytest.raises(
        RuntimeError,
        match="JWT_SECRET",
    ):
        validate_production_security(
            _settings(
                jwt_secret="too-short",
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



def test_production_requires_hsts():
    with pytest.raises(
        RuntimeError,
        match="SECURE_HEADERS_HSTS_ENABLED",
    ):
        validate_production_security(
            _settings(
                secure_headers_hsts_enabled=False,
            )
        )



def test_production_requires_auth_rate_limiting():
    with pytest.raises(
        RuntimeError,
        match="AUTH_RATE_LIMIT_ENABLED",
    ):
        validate_production_security(
            _settings(
                auth_rate_limit_enabled=False,
            )
        )



def test_production_requires_explicit_trusted_proxy():
    with pytest.raises(
        RuntimeError,
        match="FORWARDED_ALLOW_IPS",
    ):
        validate_production_security(
            _settings(
                forwarded_allow_ips="",
            )
        )


def test_production_rejects_forwarded_allow_all():
    with pytest.raises(
        RuntimeError,
        match="FORWARDED_ALLOW_IPS",
    ):
        validate_production_security(
            _settings(
                forwarded_allow_ips="*",
            )
        )


def test_production_rejects_wildcard_in_proxy_list():
    with pytest.raises(
        RuntimeError,
        match="FORWARDED_ALLOW_IPS",
    ):
        validate_production_security(
            _settings(
                forwarded_allow_ips=(
                    "172.20.0.10,*"
                ),
            )
        )


def test_production_accepts_explicit_proxy_network():
    validate_production_security(
        _settings(
            forwarded_allow_ips="172.20.0.0/24",
        )
    )
