import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.observability.metrics import observe_http_request


UNMATCHED_ROUTE = "__unmatched__"
METRICS_PATH = "/metrics"


def _request_route_label(request: Request) -> str:
    route = request.scope.get("route")
    route_path = getattr(route, "path", None)

    if isinstance(route_path, str) and route_path:
        return route_path

    return UNMATCHED_ROUTE


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = (
            request.headers.get("x-request-id")
            or str(uuid.uuid4())
        )

        request.state.request_id = request_id
        started = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            elapsed = time.perf_counter() - started

            if request.url.path != METRICS_PATH:
                observe_http_request(
                    method=request.method,
                    route=_request_route_label(request),
                    status_code=500,
                    duration_seconds=elapsed,
                )

            raise

        elapsed = time.perf_counter() - started

        response.headers["x-request-id"] = request_id
        response.headers["x-process-time-ms"] = (
            f"{elapsed * 1000:.2f}"
        )

        if request.url.path != METRICS_PATH:
            observe_http_request(
                method=request.method,
                route=_request_route_label(request),
                status_code=response.status_code,
                duration_seconds=elapsed,
            )

        return response
