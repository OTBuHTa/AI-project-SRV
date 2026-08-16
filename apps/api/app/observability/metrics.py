from prometheus_client import (
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)
from prometheus_client.exposition import CONTENT_TYPE_LATEST


REGISTRY = CollectorRegistry(auto_describe=True)

HTTP_REQUESTS = Counter(
    "srv_http_requests",
    "Total HTTP requests handled by the API.",
    (
        "method",
        "route",
        "status_code",
    ),
    registry=REGISTRY,
)

HTTP_REQUEST_DURATION = Histogram(
    "srv_http_request_duration_seconds",
    "HTTP request processing duration in seconds.",
    (
        "method",
        "route",
        "status_code",
    ),
    buckets=(
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
    ),
    registry=REGISTRY,
)


def observe_http_request(
    *,
    method: str,
    route: str,
    status_code: int,
    duration_seconds: float,
) -> None:
    labels = {
        "method": method,
        "route": route,
        "status_code": str(status_code),
    }

    HTTP_REQUESTS.labels(**labels).inc()

    HTTP_REQUEST_DURATION.labels(
        **labels,
    ).observe(duration_seconds)


def render_metrics() -> bytes:
    return generate_latest(REGISTRY)


__all__ = [
    "CONTENT_TYPE_LATEST",
    "HTTP_REQUEST_DURATION",
    "HTTP_REQUESTS",
    "REGISTRY",
    "observe_http_request",
    "render_metrics",
]
