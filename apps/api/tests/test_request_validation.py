from fastapi.testclient import TestClient

from app.main import app


client = TestClient(
    app,
    raise_server_exceptions=False,
)


def test_malformed_unicode_email_returns_422():
    response = client.post(
        "/api/v1/auth/login",
        content=(
            b'{"email":"bad\\udcd0@example.com",'
            b'"password":"irrelevant"}'
        ),
        headers={
            "content-type": "application/json",
        },
    )

    assert response.status_code == 422

    payload = response.json()
    detail = payload["detail"]

    assert isinstance(detail, list)
    assert detail

    assert all(
        "input" not in error
        for error in detail
    )

    response.content.decode("utf-8")


def test_validation_error_does_not_echo_password():
    response = client.post(
        "/api/v1/auth/bootstrap",
        json={
            "email": "owner@example.com",
            "password": "p@ssw0rd",
            "display_name": "Owner",
            "organization_name": "Test Org",
            "organization_slug": "test-org",
            "workspace_name": "Main",
        },
    )

    assert response.status_code == 422
    assert "p@ssw0rd" not in response.text

    detail = response.json()["detail"]

    assert all(
        "input" not in error
        for error in detail
    )
