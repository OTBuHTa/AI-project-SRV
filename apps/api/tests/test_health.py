from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_root():
    response = client.get("/api/v1")
    assert response.status_code == 200
    assert response.json()["version"] == "0.1.7-alpha"
