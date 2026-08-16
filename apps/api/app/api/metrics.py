from fastapi import APIRouter, Response

from app.observability.metrics import (
    CONTENT_TYPE_LATEST,
    render_metrics,
)


router = APIRouter(tags=["system"])


@router.get(
    "/metrics",
    include_in_schema=False,
)
def metrics() -> Response:
    return Response(
        content=render_metrics(),
        media_type=CONTENT_TYPE_LATEST,
    )
