from ipaddress import ip_address
from pathlib import Path
import re

from app.core.config import Settings
from app.core.startup_security import (
    validate_production_security,
)


_FQDN_LABEL = re.compile(
    r"^[A-Za-z0-9]"
    r"(?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$"
)


def _decode_env_value(value: str) -> str:
    value = value.strip()

    if (
        len(value) >= 2
        and value[0] == value[-1]
        and value[0] in {"'", '"'}
    ):
        return value[1:-1]

    return value


def _read_env_values(
    path: str | Path,
) -> dict[str, str]:
    env_path = Path(path)

    if not env_path.is_file():
        raise RuntimeError(
            "environment file not found: "
            f"{env_path}"
        )

    values: dict[str, str] = {}

    for line_number, raw in enumerate(
        env_path.read_text().splitlines(),
        start=1,
    ):
        line = raw.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line[7:].lstrip()

        if "=" not in line:
            raise RuntimeError(
                "invalid environment line "
                f"{line_number}: missing '='"
            )

        key, value = line.split("=", 1)
        key = key.strip()

        if not key:
            raise RuntimeError(
                "invalid environment line "
                f"{line_number}: empty key"
            )

        values[key] = _decode_env_value(
            value,
        )

    return values


def load_settings_from_env_file(
    path: str | Path,
) -> Settings:
    raw_values = _read_env_values(path)

    values = {
        name: field.get_default(
            call_default_factory=True,
        )
        for name, field
        in Settings.model_fields.items()
    }

    field_names = {
        name.upper(): name
        for name in Settings.model_fields
    }

    for key, value in raw_values.items():
        field_name = field_names.get(key)

        if field_name is None:
            continue

        values[field_name] = value

    return Settings(
        _env_file=None,
        **values,
    )


def validate_production_env_file(
    path: str | Path,
) -> Settings:
    settings = load_settings_from_env_file(
        path,
    )

    if settings.app_env.lower() != "production":
        raise RuntimeError(
            "APP_ENV must be production for "
            "production preflight"
        )

    validate_production_security(settings)

    return settings


def _required_value(
    values: dict[str, str],
    name: str,
) -> str:
    value = values.get(name, "").strip()

    if not value:
        raise RuntimeError(
            f"{name} is required"
        )

    return value


def _validate_server_name(
    value: str,
) -> None:
    hostname = value.rstrip(".")
    lowered = hostname.lower()

    if lowered in {
        "localhost",
        "replace-with-fqdn.example",
    }:
        raise RuntimeError(
            "AI_SRV_SERVER_NAME must be a "
            "real production FQDN"
        )

    if (
        "://" in hostname
        or "/" in hostname
        or any(
            char.isspace()
            for char in hostname
        )
    ):
        raise RuntimeError(
            "AI_SRV_SERVER_NAME must contain "
            "only a hostname"
        )

    try:
        ip_address(hostname)
    except ValueError:
        pass
    else:
        raise RuntimeError(
            "AI_SRV_SERVER_NAME must be an "
            "FQDN, not an IP address"
        )

    labels = hostname.split(".")

    if (
        len(labels) < 2
        or any(
            not _FQDN_LABEL.fullmatch(label)
            for label in labels
        )
    ):
        raise RuntimeError(
            "AI_SRV_SERVER_NAME is not a "
            "valid FQDN"
        )


def _validate_tls_file(
    value: str,
    name: str,
) -> Path:
    path = Path(value)

    if not path.is_absolute():
        raise RuntimeError(
            f"{name} must be an absolute path"
        )

    if not path.is_file():
        raise RuntimeError(
            f"{name} file not found: {path}"
        )

    return path


def validate_production_deployment_profile(
    path: str | Path,
) -> Settings:
    settings = validate_production_env_file(
        path,
    )

    values = _read_env_values(path)

    env_file = _required_value(
        values,
        "AI_SRV_ENV_FILE",
    )

    if Path(env_file).name != ".env.production":
        raise RuntimeError(
            "AI_SRV_ENV_FILE must reference "
            ".env.production"
        )

    server_name = _required_value(
        values,
        "AI_SRV_SERVER_NAME",
    )
    _validate_server_name(server_name)

    cert_path = _validate_tls_file(
        _required_value(
            values,
            "AI_SRV_TLS_CERT_PATH",
        ),
        "AI_SRV_TLS_CERT_PATH",
    )

    key_path = _validate_tls_file(
        _required_value(
            values,
            "AI_SRV_TLS_KEY_PATH",
        ),
        "AI_SRV_TLS_KEY_PATH",
    )

    if cert_path == key_path:
        raise RuntimeError(
            "TLS certificate and private key "
            "must use different files"
        )

    return settings
