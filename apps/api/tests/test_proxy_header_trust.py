import asyncio

from uvicorn.middleware.proxy_headers import (
    ProxyHeadersMiddleware,
)


async def _resolved_scope(
    *,
    peer_host: str,
    forwarded_for: str,
    trusted_hosts: str,
):
    captured = {}

    async def app(scope, receive, send):
        captured.update(scope)

    middleware = ProxyHeadersMiddleware(
        app,
        trusted_hosts=trusted_hosts,
    )

    scope = {
        "type": "http",
        "asgi": {
            "version": "3.0",
            "spec_version": "2.3",
        },
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "root_path": "",
        "headers": [
            (
                b"x-forwarded-for",
                forwarded_for.encode("ascii"),
            ),
        ],
        "client": (peer_host, 50000),
        "server": ("api", 8000),
    }

    async def receive():
        return {
            "type": "http.disconnect",
        }

    async def send(message):
        pass

    await middleware(scope, receive, send)

    return captured


def test_untrusted_peer_cannot_spoof_forwarded_client():
    scope = asyncio.run(
        _resolved_scope(
            peer_host="198.51.100.10",
            forwarded_for="203.0.113.55",
            trusted_hosts="172.20.0.10",
        )
    )

    assert scope["client"][0] == "198.51.100.10"


def test_trusted_proxy_can_supply_client_address():
    scope = asyncio.run(
        _resolved_scope(
            peer_host="172.20.0.10",
            forwarded_for="203.0.113.55",
            trusted_hosts="172.20.0.10",
        )
    )

    assert scope["client"][0] == "203.0.113.55"


def test_trusted_proxy_cidr_is_supported():
    scope = asyncio.run(
        _resolved_scope(
            peer_host="172.20.0.10",
            forwarded_for="203.0.113.55",
            trusted_hosts="172.20.0.0/24",
        )
    )

    assert scope["client"][0] == "203.0.113.55"


def test_forwarded_chain_selects_first_untrusted_client():
    scope = asyncio.run(
        _resolved_scope(
            peer_host="172.20.0.10",
            forwarded_for=(
                "203.0.113.55, 172.20.0.11"
            ),
            trusted_hosts="172.20.0.0/24",
        )
    )

    assert scope["client"][0] == "203.0.113.55"
