from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_metrics_exposes_http_request_metrics():
    response = client.get("/health")

    assert response.status_code == 200

    metrics = client.get("/metrics")

    assert metrics.status_code == 200

    content_type = metrics.headers["content-type"]

    assert content_type.startswith(
        "text/plain"
    )

    body = metrics.text

    assert (
        'srv_http_requests_total{'
        'method="GET",'
        'route="/health",'
        'status_code="200"}'
    ) in body

    assert (
        'srv_http_request_duration_seconds_count{'
        'method="GET",'
        'route="/health",'
        'status_code="200"}'
    ) in body


def test_metrics_endpoint_does_not_self_instrument():
    client.get("/metrics")
    client.get("/metrics")

    body = client.get("/metrics").text

    assert 'route="/metrics"' not in body


def test_unmatched_request_uses_bounded_route_label():
    path = "/not-found/high-cardinality-value-123"

    response = client.get(path)

    assert response.status_code == 404

    body = client.get("/metrics").text

    assert (
        'srv_http_requests_total{'
        'method="GET",'
        'route="__unmatched__",'
        'status_code="404"}'
    ) in body

    assert path not in body


def test_metrics_is_not_exposed_in_openapi():
    schema = app.openapi()

    assert "/metrics" not in schema["paths"]


def test_dynamic_route_uses_template_label():
    agent_id = "11111111-1111-1111-1111-111111111111"
    path = f"/api/v1/agents/{agent_id}/revoke"

    response = client.post(path)

    assert response.status_code in {401, 403, 422}

    body = client.get("/metrics").text

    assert (
        'method="POST",'
        'route="/api/v1/agents/{agent_id}/revoke"'
    ) in body
    assert agent_id not in body
