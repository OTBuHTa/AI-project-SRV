from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from ai_srv_agent.main import collect_inventory, submit_inventory


def test_collect_inventory_contains_core_items():
    partitions = [
        SimpleNamespace(
            mountpoint="/",
            device="/dev/sda1",
            fstype="ext4",
            opts="rw",
        )
    ]

    usage = SimpleNamespace(
        total=1000,
        used=400,
        free=600,
        percent=40.0,
    )

    address = SimpleNamespace(
        family=2,
        address="192.168.1.10",
        netmask="255.255.255.0",
        broadcast="192.168.1.255",
    )

    net_stat = SimpleNamespace(
        isup=True,
        speed=1000,
        mtu=1500,
    )

    memory = SimpleNamespace(
        total=16000,
        available=8000,
    )

    frequency = SimpleNamespace(
        current=3200.0,
    )

    docker = {
        "available": True,
        "containers_total": 1,
        "containers_running": 1,
        "containers_stopped": 0,
        "containers": [
            {
                "id": "abc123",
                "name": "api",
                "image": "example/api:latest",
                "status": "Up 10 minutes",
                "state": "running",
            }
        ],
    }

    with (
        patch(
            "ai_srv_agent.main.psutil.cpu_count",
            side_effect=[8, 4],
        ),
        patch(
            "ai_srv_agent.main.psutil.cpu_freq",
            return_value=frequency,
        ),
        patch(
            "ai_srv_agent.main.psutil.virtual_memory",
            return_value=memory,
        ),
        patch(
            "ai_srv_agent.main.psutil.disk_partitions",
            return_value=partitions,
        ),
        patch(
            "ai_srv_agent.main.psutil.disk_usage",
            return_value=usage,
        ),
        patch(
            "ai_srv_agent.main.psutil.net_if_addrs",
            return_value={"eth0": [address]},
        ),
        patch(
            "ai_srv_agent.main.psutil.net_if_stats",
            return_value={"eth0": net_stat},
        ),
        patch(
            "ai_srv_agent.main.collect_docker",
            return_value=docker,
        ),
    ):
        items = collect_inventory()

    identities = {
        (item["kind"], item["external_id"])
        for item in items
    }

    assert ("cpu", "cpu") in identities
    assert ("memory", "memory") in identities
    assert ("filesystem", "/") in identities
    assert ("network_interface", "eth0") in identities
    assert ("docker_engine", "docker") in identities
    assert ("docker_container", "api") in identities


def test_submit_inventory_uses_agent_identity():
    state = {
        "api_url": "https://example.test",
        "agent_id": "agent-id",
        "agent_token": "secret-token",
    }

    response = MagicMock()

    with (
        patch(
            "ai_srv_agent.main.collect_inventory",
            return_value=[],
        ),
        patch(
            "ai_srv_agent.main.httpx.post",
            return_value=response,
        ) as post,
    ):
        submit_inventory(state)

    post.assert_called_once()

    args, kwargs = post.call_args

    assert args[0] == (
        "https://example.test/api/v1/agents/"
        "agent-id/inventory"
    )

    assert kwargs["json"] == {"items": []}
    assert kwargs["headers"] == {
        "Authorization": "Bearer secret-token",
    }

    response.raise_for_status.assert_called_once()
