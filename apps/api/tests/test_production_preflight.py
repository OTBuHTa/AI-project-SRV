import pytest

from app.core.production_preflight import (
    validate_production_deployment_profile,
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



def _deployment_env(
    tmp_path,
    *,
    server_name="srv.example.com",
):
    cert = tmp_path / "fullchain.pem"
    key = tmp_path / "privkey.pem"

    cert.write_text("test certificate")
    key.write_text("test private key")

    return (
        HARDENED_ENV
        + "\nAI_SRV_ENV_FILE=.env.production"
        + f"\nAI_SRV_SERVER_NAME={server_name}"
        + f"\nAI_SRV_TLS_CERT_PATH={cert}"
        + f"\nAI_SRV_TLS_KEY_PATH={key}"
        + "\n"
    )


def test_deployment_preflight_accepts_tls_profile(
    tmp_path,
):
    env_file = tmp_path / ".env.production"

    env_file.write_text(
        _deployment_env(tmp_path)
    )

    settings = (
        validate_production_deployment_profile(
            env_file,
        )
    )

    assert settings.app_env == "production"


def test_deployment_preflight_rejects_placeholder_fqdn(
    tmp_path,
):
    env_file = tmp_path / ".env.production"

    env_file.write_text(
        _deployment_env(
            tmp_path,
            server_name=(
                "replace-with-fqdn.example"
            ),
        )
    )

    with pytest.raises(
        RuntimeError,
        match="real production FQDN",
    ):
        validate_production_deployment_profile(
            env_file,
        )


def test_deployment_preflight_rejects_missing_tls_file(
    tmp_path,
):
    env_file = tmp_path / ".env.production"

    content = _deployment_env(tmp_path)

    missing = tmp_path / "missing.pem"

    content = content.replace(
        str(tmp_path / "fullchain.pem"),
        str(missing),
    )

    env_file.write_text(content)

    with pytest.raises(
        RuntimeError,
        match="file not found",
    ):
        validate_production_deployment_profile(
            env_file,
        )
