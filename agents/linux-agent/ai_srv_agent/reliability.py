import random
import time
from collections.abc import Callable
from typing import TypeVar

import httpx

T = TypeVar("T")

RETRYABLE_STATUS_CODES = {408, 425, 429}


def is_retryable_http_error(exc: Exception) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        return status_code in RETRYABLE_STATUS_CODES or status_code >= 500
    return False


def retry_http(
    operation: Callable[[], T],
    *,
    attempts: int = 4,
    base_delay_seconds: float = 1.0,
    max_delay_seconds: float = 30.0,
    sleep: Callable[[float], None] = time.sleep,
    random_value: Callable[[], float] = random.random,
) -> T:
    if attempts < 1:
        raise ValueError("attempts must be at least 1")

    for attempt in range(attempts):
        try:
            return operation()
        except Exception as exc:
            if attempt == attempts - 1 or not is_retryable_http_error(exc):
                raise

            exponential_delay = min(
                max_delay_seconds,
                base_delay_seconds * (2**attempt),
            )
            jittered_delay = exponential_delay * (0.5 + random_value() * 0.5)
            sleep(jittered_delay)

    raise RuntimeError("unreachable")
