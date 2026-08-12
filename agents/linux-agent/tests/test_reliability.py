from unittest.mock import MagicMock

import httpx
import pytest

from ai_srv_agent.reliability import retry_http


def test_retry_http_retries_transport_error_with_exponential_backoff():
    operation = MagicMock(
        side_effect=[httpx.ConnectError("offline"), httpx.ReadTimeout("slow"), "ok"]
    )
    delays = []

    result = retry_http(
        operation,
        attempts=4,
        base_delay_seconds=2,
        sleep=delays.append,
        random_value=lambda: 1.0,
    )

    assert result == "ok"
    assert operation.call_count == 3
    assert delays == [2, 4]


def test_retry_http_retries_server_error():
    request = httpx.Request("GET", "https://example.test")
    response = httpx.Response(503, request=request)
    operation = MagicMock(side_effect=[httpx.HTTPStatusError("down", request=request, response=response), "ok"])

    assert retry_http(operation, sleep=lambda _: None) == "ok"
    assert operation.call_count == 2


def test_retry_http_does_not_retry_client_error():
    request = httpx.Request("GET", "https://example.test")
    response = httpx.Response(401, request=request)
    error = httpx.HTTPStatusError("unauthorized", request=request, response=response)
    operation = MagicMock(side_effect=error)

    with pytest.raises(httpx.HTTPStatusError):
        retry_http(operation, sleep=lambda _: None)

    operation.assert_called_once()
