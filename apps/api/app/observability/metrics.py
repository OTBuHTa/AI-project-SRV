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


from prometheus_client import Gauge

from app.services.notification_delivery_observability import (
    get_notification_delivery_operational_snapshot,
)


NOTIFICATION_DELIVERIES = Gauge(
    "srv_notification_deliveries",
    "Current persisted notification deliveries by source and status.",
    (
        "source",
        "status",
    ),
    registry=REGISTRY,
)

NOTIFICATION_DELIVERY_PROBLEMS = Gauge(
    "srv_notification_delivery_problems",
    "Current notification delivery problems by source and classification.",
    (
        "source",
        "problem",
    ),
    registry=REGISTRY,
)

NOTIFICATION_OLDEST_PENDING_AGE = Gauge(
    "srv_notification_oldest_pending_age_seconds",
    "Age in seconds of the oldest pending notification delivery.",
    ("source",),
    registry=REGISTRY,
)

NOTIFICATION_METRICS_COLLECTION_SUCCESS = Gauge(
    "srv_notification_metrics_collection_success",
    "Whether notification delivery metrics were collected successfully.",
    registry=REGISTRY,
)


DELIVERY_STATUSES = (
    "pending",
    "sending",
    "delivered",
    "failed",
    "canceled",
)

DELIVERY_PROBLEMS = (
    "retryable_failed",
    "exhausted_failed",
    "stale_sending",
)


def collect_notification_delivery_metrics(db) -> None:
    snapshot = get_notification_delivery_operational_snapshot(
        db
    )

    NOTIFICATION_DELIVERIES.clear()
    NOTIFICATION_DELIVERY_PROBLEMS.clear()
    NOTIFICATION_OLDEST_PENDING_AGE.clear()

    for source, data in (
        ("backup", snapshot.backup),
        ("agent_lifecycle", snapshot.agent_lifecycle),
    ):
        for status in DELIVERY_STATUSES:
            NOTIFICATION_DELIVERIES.labels(
                source=source,
                status=status,
            ).set(
                getattr(data.counts, status)
            )

        for problem in DELIVERY_PROBLEMS:
            NOTIFICATION_DELIVERY_PROBLEMS.labels(
                source=source,
                problem=problem,
            ).set(
                getattr(data.counts, problem)
            )

        NOTIFICATION_OLDEST_PENDING_AGE.labels(
            source=source,
        ).set(
            data.oldest_pending_age_seconds
        )

    NOTIFICATION_METRICS_COLLECTION_SUCCESS.set(1)


def clear_notification_delivery_metrics() -> None:
    NOTIFICATION_DELIVERIES.clear()
    NOTIFICATION_DELIVERY_PROBLEMS.clear()
    NOTIFICATION_OLDEST_PENDING_AGE.clear()

    NOTIFICATION_METRICS_COLLECTION_SUCCESS.set(0)
