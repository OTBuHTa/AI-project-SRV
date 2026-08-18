from fastapi.testclient import TestClient

from app.api import health as health_api
from app.main import app
from app.version import API_VERSION

client = TestClient(app)


def test_health_exposes_runtime_identity(monkeypatch):
    monkeypatch.setattr(
        health_api.settings,
        "app_build_revision",
        "abc123def456",
    )

    response = client.get("/health")

    assert response.status_code == 200

    payload = response.json()

    assert payload["version"] == API_VERSION
    assert payload["build_revision"] == "abc123def456"
    assert payload["service"] == "AI-project SRV"


def test_api_root_exposes_runtime_identity(monkeypatch):
    import app.main as main_module

    monkeypatch.setattr(
        main_module.settings,
        "app_build_revision",
        "abc123def456",
    )

    response = client.get("/api/v1")

    assert response.status_code == 200

    payload = response.json()

    assert payload["version"] == API_VERSION
    assert payload["build_revision"] == "abc123def456"


def test_build_revision_defaults_to_unknown():
    from app.core.config import Settings

    settings = Settings(_env_file=None)

    assert settings.app_build_revision == "unknown"
