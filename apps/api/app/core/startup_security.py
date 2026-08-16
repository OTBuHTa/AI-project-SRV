from app.core.config import Settings


DEFAULT_JWT_SECRET = "change-me-before-external-access"


def validate_production_security(
    settings: Settings,
) -> None:
    if settings.app_env.lower() != "production":
        return

    errors: list[str] = []

    if (
        not settings.jwt_secret
        or settings.jwt_secret == DEFAULT_JWT_SECRET
    ):
        errors.append(
            "JWT_SECRET must be set to a strong non-default value"
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
