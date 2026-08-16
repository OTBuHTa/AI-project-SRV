import logging
import secrets

from fastapi import APIRouter, Header, HTTPException, Response, status

from app.core.config import get_settings
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
settings = get_settings()


def _require_metrics_auth(
    authorization: str | None,
) -> None:
    configured_token = settings.metrics_bearer_token

    if not configured_token:
        return

    scheme, separator, presented_token = (
        authorization or ""
    ).partition(" ")

    valid = (
        separator == " "
        and scheme.lower() == "bearer"
        and bool(presented_token)
        and secrets.compare_digest(
            presented_token,
            configured_token,
        )
    )

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="metrics_authentication_required",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )


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
def metrics(
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
    ),
) -> Response:
    _require_metrics_auth(authorization)

    _collect_notification_metrics()
    _collect_worker_metrics()

    return Response(
        content=render_metrics(),
        media_type=CONTENT_TYPE_LATEST,
    )
