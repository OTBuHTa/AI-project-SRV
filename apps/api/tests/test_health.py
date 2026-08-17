from fastapi.testclient import TestClient
from app.main import app
from app.version import API_VERSION

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_root():
    response = client.get("/api/v1")
    assert response.status_code == 200
    assert response.json()["version"] == API_VERSION
    assert app.version == API_VERSION
