from types import SimpleNamespace

from fastapi import Response

from app.api.v1.auth import (
    _disable_sensitive_response_caching,
)


def test_sensitive_response_disables_caching():
    response = Response()

    _disable_sensitive_response_caching(response)

    assert response.headers["cache-control"] == "no-store"
    assert response.headers["pragma"] == "no-cache"


def test_sensitive_response_overrides_existing_cache_policy():
    response = Response()

    response.headers["Cache-Control"] = "public, max-age=3600"
    response.headers["Pragma"] = "cache"

    _disable_sensitive_response_caching(response)

    assert response.headers["cache-control"] == "no-store"
    assert response.headers["pragma"] == "no-cache"
