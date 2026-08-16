from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _assert_security_headers(response) -> None:
    assert (
        response.headers["x-content-type-options"]
        == "nosniff"
    )
    assert response.headers["x-frame-options"] == "DENY"
    assert (
        response.headers["referrer-policy"]
        == "no-referrer"
    )
    assert (
        response.headers["permissions-policy"]
        == "camera=(), microphone=(), geolocation=()"
    )


def test_health_has_security_headers():
    response = client.get("/health")

    assert response.status_code == 200
    _assert_security_headers(response)


def test_ready_has_security_headers():
    response = client.get("/ready")

    assert response.status_code in {200, 503}
    _assert_security_headers(response)


def test_api_error_has_security_headers():
    response = client.get(
        "/api/v1/workspaces",
    )

    assert response.status_code == 401
    _assert_security_headers(response)


def test_unmatched_route_has_security_headers():
    response = client.get(
        "/security-header-not-found",
    )

    assert response.status_code == 404
    _assert_security_headers(response)


def test_hsts_is_disabled_by_default(monkeypatch):
    import app.middleware.security_headers as security_headers

    monkeypatch.setattr(
        security_headers.settings,
        "secure_headers_hsts_enabled",
        False,
    )

    response = client.get("/health")

    assert "strict-transport-security" not in response.headers


def test_hsts_is_emitted_when_enabled(monkeypatch):
    import app.middleware.security_headers as security_headers

    monkeypatch.setattr(
        security_headers.settings,
        "secure_headers_hsts_enabled",
        True,
    )

    response = client.get("/health")

    assert (
        response.headers["strict-transport-security"]
        == "max-age=31536000; includeSubDomains"
    )
