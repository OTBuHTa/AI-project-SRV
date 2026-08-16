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
