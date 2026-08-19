import json

import httpx
import pytest

from app.core.config import Settings
from app.services.mikrotik import (
    MikroTikConfigurationError,
    MikroTikDisabledError,
    MikroTikError,
    MikroTikClient,
)


def _settings(**overrides):
    values = {
        "mikrotik_enabled": True,
        "mikrotik_base_url": "https://192.0.2.1",
        "mikrotik_username": "automation",
        "mikrotik_password": "secret",
        "mikrotik_verify_tls": True,
        "mikrotik_timeout_seconds": 2.0,
        "mikrotik_wan_interface": "ether1",
        "mikrotik_expected_wan_ip": "198.51.100.2",
    }
    values.update(overrides)
    return Settings(**values)


def test_disabled_integration_is_rejected():
    with pytest.raises(MikroTikDisabledError):
        MikroTikClient(
            _settings(mikrotik_enabled=False)
        )


def test_plain_http_is_rejected():
    with pytest.raises(MikroTikConfigurationError):
        MikroTikClient(
            _settings(
                mikrotik_base_url="http://192.0.2.1"
            )
        )


def test_missing_wan_interface_is_rejected():
    with pytest.raises(
        MikroTikConfigurationError,
        match="mikrotik_wan_interface_required",
    ):
        MikroTikClient(
            _settings(mikrotik_wan_interface="")
        )


def test_status_reads_only_expected_routeros_menus():
    payloads = {
        "/rest/system/identity": [{"name": "home-router"}],
        "/rest/system/resource": [
            {
                "version": "7.20",
                "uptime": "1d",
                "cpu-load": "3",
                "free-memory": "1000",
            }
        ],
        "/rest/interface": [
            {"name": "ether1", "running": "true"},
            {"name": "bridge", "running": "true"},
        ],
        "/rest/ip/address": [
            {"address": "192.168.88.1/24"}
        ],
        "/rest/ip/route": [
            {
                "dst-address": "0.0.0.0/0",
                "inactive": "false",
                "disabled": "false",
            }
        ],
        "/rest/ip/dhcp-client": [
            {
                ".id": "*1",
                "interface": "ether1",
                "status": "bound",
                "address": "198.51.100.2/24",
                "gateway": "198.51.100.1",
            }
        ],
        "/rest/ip/dns": [
            {"servers": "1.1.1.1"}
        ],
    }

    def handler(request: httpx.Request):
        body = payloads[request.url.path]
        return httpx.Response(
            200,
            content=json.dumps(body).encode(),
            headers={"content-type": "application/json"},
        )

    transport = httpx.MockTransport(handler)

    with MikroTikClient(
        _settings(),
        transport=transport,
    ) as client:
        status = client.status()

    assert status["connected"] is True
    assert status["identity"] == "home-router"
    assert status["default_route_present"] is True
    assert status["dhcp_clients"][0]["status"] == "bound"
    assert status["wan_interface"] == "ether1"
    assert status["wan_running"] is True
    assert status["wan_dhcp_bound"] is True
    assert status["wan_address"] == "198.51.100.2"
    assert status["expected_wan_ip"] == "198.51.100.2"
    assert status["wan_ip_matches_expected"] is True


def test_status_reports_wan_ip_drift():
    payloads = {
        "/rest/system/identity": [{}],
        "/rest/system/resource": [{}],
        "/rest/interface": [
            {"name": "ether1", "running": "true"}
        ],
        "/rest/ip/address": [],
        "/rest/ip/route": [],
        "/rest/ip/dhcp-client": [
            {
                "interface": "ether1",
                "status": "bound",
                "address": "198.51.100.99/24",
            }
        ],
        "/rest/ip/dns": [{}],
    }

    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json=payloads[request.url.path],
        )
    )

    with MikroTikClient(
        _settings(),
        transport=transport,
    ) as client:
        status = client.status()

    assert status["wan_ip_matches_expected"] is False


def test_dhcp_renew_uses_routeros_id_not_user_input():
    calls = []

    def handler(request: httpx.Request):
        calls.append(request)
        if request.method == "GET":
            body = [
                {
                    ".id": "*A",
                    "interface": "ether1",
                    "status": "bound",
                }
            ]
            return httpx.Response(
                200,
                json=body,
            )

        assert request.url.path == (
            "/rest/ip/dhcp-client/renew"
        )
        assert json.loads(request.content) == {
            "numbers": "*A"
        }
        return httpx.Response(200, json=[])

    transport = httpx.MockTransport(handler)

    with MikroTikClient(
        _settings(),
        transport=transport,
    ) as client:
        result = client.renew_dhcp("ether1")

    assert result["interface"] == "ether1"
    assert [call.method for call in calls] == [
        "GET",
        "POST",
    ]


def test_dhcp_renew_requires_known_client():
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(
            200,
            json=[],
        )
    )

    with MikroTikClient(
        _settings(),
        transport=transport,
    ) as client:
        with pytest.raises(
            MikroTikError,
            match="routeros_dhcp_client_not_found",
        ):
            client.renew_dhcp("ether9")
