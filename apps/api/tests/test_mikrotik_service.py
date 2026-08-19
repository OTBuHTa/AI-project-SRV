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
            {"name": "ether1"},
            {"name": "bridge"},
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
