from app.services.action_verification import _container_state


def test_container_state_running():
    docker = {"containers": [{"name": "api", "state": "running"}]}
    assert _container_state(docker, "api") == "running"


def test_container_state_missing():
    docker = {"containers": [{"name": "db", "state": "running"}]}
    assert _container_state(docker, "api") is None
