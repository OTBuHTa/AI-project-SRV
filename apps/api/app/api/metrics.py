import logging

from fastapi import APIRouter, Response

from app.db.session import SessionLocal
from app.observability.metrics import (
    CONTENT_TYPE_LATEST,
    clear_notification_delivery_metrics,
    clear_worker_operational_metrics,
    collect_notification_delivery_metrics,
    collect_worker_operational_metrics,
    render_metrics,
)


logger = logging.getLogger(__name__)

router = APIRouter(tags=["system"])


def _collect_notification_metrics() -> None:
    try:
        with SessionLocal() as db:
            collect_notification_delivery_metrics(db)
    except Exception:
        clear_notification_delivery_metrics()

        logger.exception(
            "notification delivery metrics collection failed"
        )


def _collect_worker_metrics() -> None:
    try:
        with SessionLocal() as db:
            collect_worker_operational_metrics(db)
    except Exception:
        clear_worker_operational_metrics()

        logger.exception(
            "worker operational metrics collection failed"
        )


@router.get(
    "/metrics",
    include_in_schema=False,
)
def metrics() -> Response:
    _collect_notification_metrics()
    _collect_worker_metrics()

    return Response(
        content=render_metrics(),
        media_type=CONTENT_TYPE_LATEST,
    )
