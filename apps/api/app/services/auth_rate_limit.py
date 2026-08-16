import hashlib

from redis import Redis


KEY_PREFIX = "aisrv:auth:login"


def account_fingerprint(email: str) -> str:
    normalized = email.strip().lower()

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


def _ip_key(source_ip: str) -> str:
    fingerprint = hashlib.sha256(
        source_ip.encode("utf-8")
    ).hexdigest()

    return f"{KEY_PREFIX}:ip:{fingerprint}"


def _account_key(email: str) -> str:
    return (
        f"{KEY_PREFIX}:account:"
        f"{account_fingerprint(email)}"
    )


def _current_count(redis: Redis, key: str) -> int:
    value = redis.get(key)

    if value is None:
        return 0

    return int(value)


def login_rate_limit_exceeded(
    redis: Redis,
    *,
    source_ip: str,
    email: str,
    ip_limit: int,
    account_limit: int,
) -> bool:
    return (
        _current_count(redis, _ip_key(source_ip))
        >= ip_limit
        or _current_count(
            redis,
            _account_key(email),
        )
        >= account_limit
    )


def _increment_with_expiry(
    redis: Redis,
    *,
    key: str,
    window_seconds: int,
) -> None:
    pipeline = redis.pipeline(transaction=True)

    pipeline.incr(key)
    pipeline.expire(
        key,
        window_seconds,
        nx=True,
    )
    pipeline.execute()


def record_failed_login(
    redis: Redis,
    *,
    source_ip: str,
    email: str,
    window_seconds: int,
) -> None:
    _increment_with_expiry(
        redis,
        key=_ip_key(source_ip),
        window_seconds=window_seconds,
    )
    _increment_with_expiry(
        redis,
        key=_account_key(email),
        window_seconds=window_seconds,
    )


def clear_account_login_failures(
    redis: Redis,
    *,
    email: str,
) -> None:
    redis.delete(
        _account_key(email),
    )
