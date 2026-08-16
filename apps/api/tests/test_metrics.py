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


def test_notification_operational_metrics_have_bounded_labels(
    monkeypatch,
):
    from types import SimpleNamespace

    import app.observability.metrics as metrics_module

    counts_backup = SimpleNamespace(
        total=8,
        pending=2,
        sending=1,
        delivered=3,
        failed=1,
        canceled=1,
        retryable_failed=1,
        exhausted_failed=0,
        stale_sending=1,
    )

    counts_lifecycle = SimpleNamespace(
        total=4,
        pending=0,
        sending=0,
        delivered=3,
        failed=1,
        canceled=0,
        retryable_failed=0,
        exhausted_failed=1,
        stale_sending=0,
    )

    snapshot = SimpleNamespace(
        backup=SimpleNamespace(
            counts=counts_backup,
            oldest_pending_age_seconds=90.0,
        ),
        agent_lifecycle=SimpleNamespace(
            counts=counts_lifecycle,
            oldest_pending_age_seconds=0.0,
        ),
    )

    monkeypatch.setattr(
        metrics_module,
        "get_notification_delivery_operational_snapshot",
        lambda db: snapshot,
    )

    metrics_module.collect_notification_delivery_metrics(
        object()
    )

    body = metrics_module.render_metrics().decode()

    assert (
        'srv_notification_deliveries{'
        'source="backup",status="pending"} 2.0'
    ) in body

    assert (
        'srv_notification_deliveries{'
        'source="agent_lifecycle",'
        'status="delivered"} 3.0'
    ) in body

    assert (
        'srv_notification_delivery_problems{'
        'problem="retryable_failed",'
        'source="backup"} 1.0'
    ) in body

    assert (
        'srv_notification_delivery_problems{'
        'problem="exhausted_failed",'
        'source="agent_lifecycle"} 1.0'
    ) in body

    assert (
        'srv_notification_oldest_pending_age_seconds{'
        'source="backup"} 90.0'
    ) in body

    assert (
        "srv_notification_metrics_collection_success 1.0"
        in body
    )

    assert "workspace-" not in body
    assert "delivery-" not in body


def test_metrics_collection_failure_is_visible_without_http_failure(
    monkeypatch,
):
    import app.api.metrics as metrics_api

    class FakeSession:
        def __enter__(self):
            return object()

        def __exit__(
            self,
            exc_type,
            exc,
            traceback,
        ):
            return False

    def fail_collection(db):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(
        metrics_api,
        "SessionLocal",
        lambda: FakeSession(),
    )

    monkeypatch.setattr(
        metrics_api,
        "collect_notification_delivery_metrics",
        fail_collection,
    )

    response = client.get("/metrics")

    assert response.status_code == 200

    assert (
        "srv_notification_metrics_collection_success 0.0"
        in response.text
    )
