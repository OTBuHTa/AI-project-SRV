import re

from app.core.config import Settings

FULL_GIT_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")

DEFAULT_JWT_SECRET = "change-me-before-external-access"
EXAMPLE_JWT_SECRET = (
    "replace-with-at-least-32-random-bytes-"
    "before-external-access"
)
MIN_JWT_SECRET_BYTES = 32


def validate_production_security(
    settings: Settings,
) -> None:
    if settings.app_env.lower() != "production":
        return

    errors: list[str] = []

    jwt_secret = settings.jwt_secret

    if (
        not jwt_secret
        or jwt_secret in {
            DEFAULT_JWT_SECRET,
            EXAMPLE_JWT_SECRET,
        }
        or len(jwt_secret.encode("utf-8"))
        < MIN_JWT_SECRET_BYTES
    ):
        errors.append(
            "JWT_SECRET must be a non-default value "
            "of at least 32 bytes"
        )

    if settings.bootstrap_enabled:
        errors.append(
            "BOOTSTRAP_ENABLED must be false in production"
        )

    if not settings.metrics_bearer_token:
        errors.append(
            "METRICS_BEARER_TOKEN must be configured in production"
        )

    if not settings.secure_headers_hsts_enabled:
        errors.append(
            "SECURE_HEADERS_HSTS_ENABLED must be true in production"
        )

    if not settings.auth_rate_limit_enabled:
        errors.append(
            "AUTH_RATE_LIMIT_ENABLED must be true in production"
        )

    forwarded_allow_ips = settings.forwarded_allow_ips.strip()

    if not forwarded_allow_ips:
        errors.append(
            "FORWARDED_ALLOW_IPS must explicitly identify trusted proxies"
        )
    elif "*" in {
        value.strip()
        for value in forwarded_allow_ips.split(",")
    }:
        errors.append(
            "FORWARDED_ALLOW_IPS must not trust all clients in production"
        )

    if errors:
        raise RuntimeError(
            "unsafe production security configuration: "
            + "; ".join(errors)
        )

def validate_production_build_identity(
    settings: Settings,
) -> None:
    if settings.app_env.lower() != "production":
        return

    build_revision = settings.app_build_revision.strip()

    if not FULL_GIT_SHA_PATTERN.fullmatch(
        build_revision
    ):
        raise RuntimeError(
            "unsafe production build identity: "
            "APP_BUILD_REVISION must be a full "
            "40-character lowercase Git SHA"
        )
