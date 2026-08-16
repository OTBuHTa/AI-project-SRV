import logging

from fastapi import APIRouter, Response

from app.db.session import SessionLocal
from app.observability.metrics import (
    CONTENT_TYPE_LATEST,
    clear_notification_delivery_metrics,
    collect_notification_delivery_metrics,
    render_metrics,
)


logger = logging.getLogger(__name__)

router = APIRouter(tags=["system"])


@router.get(
    "/metrics",
    include_in_schema=False,
)
def metrics() -> Response:
    try:
        with SessionLocal() as db:
            collect_notification_delivery_metrics(db)
    except Exception:
        clear_notification_delivery_metrics()

        logger.exception(
            "notification delivery metrics collection failed"
        )

    return Response(
        content=render_metrics(),
        media_type=CONTENT_TYPE_LATEST,
    )
