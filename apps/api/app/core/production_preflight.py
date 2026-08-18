from pathlib import Path

from app.core.config import Settings
from app.core.startup_security import (
    validate_production_security,
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


def load_settings_from_env_file(
    path: str | Path,
) -> Settings:
    env_path = Path(path)

    if not env_path.is_file():
        raise RuntimeError(
            "environment file not found: "
            f"{env_path}"
        )

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

        field_name = field_names.get(key)

        if field_name is None:
            continue

        values[field_name] = _decode_env_value(
            value,
        )

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
