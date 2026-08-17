from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.status import HTTP_422_UNPROCESSABLE_CONTENT


def _sanitize_validation_value(
    value: Any,
) -> Any:
    if isinstance(value, str):
        return value.encode(
            "utf-8",
            errors="replace",
        ).decode("utf-8")

    if isinstance(value, dict):
        return {
            key: _sanitize_validation_value(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            _sanitize_validation_value(item)
            for item in value
        ]

    return value


async def request_validation_exception_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors = [
        {
            key: _sanitize_validation_value(value)
            for key, value in error.items()
            if key != "input"
        }
        for error in exc.errors()
    ]

    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "detail": jsonable_encoder(errors),
        },
    )
