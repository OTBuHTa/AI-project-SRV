from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import Settings, get_settings


class MikroTikError(RuntimeError):
    """Base error for RouterOS integration failures."""


class MikroTikDisabledError(MikroTikError):
    """Raised when RouterOS automation is not enabled."""


class MikroTikConfigurationError(MikroTikError):
    """Raised when RouterOS automation settings are unsafe or incomplete."""


@dataclass(frozen=True)
class MikroTikSnapshot:
    identity: dict[str, Any]
    resource: dict[str, Any]
    interfaces: list[dict[str, Any]]
    addresses: list[dict[str, Any]]
    routes: list[dict[str, Any]]
    dhcp_clients: list[dict[str, Any]]
    dns: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity,
            "resource": self.resource,
            "interfaces": self.interfaces,
            "addresses": self.addresses,
            "routes": self.routes,
            "dhcp_clients": self.dhcp_clients,
            "dns": self.dns,
        }


def _first_record(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, list) and value and isinstance(value[0], dict):
        return value[0]
    return {}


class MikroTikClient:
    """Restricted RouterOS REST client used by AI-project SRV."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.settings = settings or get_settings()

        if not self.settings.mikrotik_enabled:
            raise MikroTikDisabledError("mikrotik_disabled")

        base_url = self.settings.mikrotik_base_url.rstrip("/")
        parsed = urlparse(base_url)

        if parsed.scheme != "https" or not parsed.hostname:
            raise MikroTikConfigurationError(
                "mikrotik_base_url_must_use_https"
            )
        if parsed.username or parsed.password:
            raise MikroTikConfigurationError(
                "mikrotik_credentials_must_not_be_in_url"
            )
        if not self.settings.mikrotik_username:
            raise MikroTikConfigurationError(
                "mikrotik_username_required"
            )
        if not self.settings.mikrotik_password:
            raise MikroTikConfigurationError(
                "mikrotik_password_required"
            )

        self._base_url = f"{base_url}/rest"
        self._client = httpx.Client(
            auth=httpx.BasicAuth(
                self.settings.mikrotik_username,
                self.settings.mikrotik_password,
            ),
            timeout=self.settings.mikrotik_timeout_seconds,
            verify=self.settings.mikrotik_verify_tls,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "MikroTikClient":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, str] | None = None,
    ) -> Any:
        url = f"{self._base_url}/{path.lstrip('/')}"
        try:
            response = self._client.request(
                method,
                url,
                json=json,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise MikroTikError(
                f"routeros_request_failed:{path}"
            ) from exc

        if not response.content:
            return []

        try:
            return response.json()
        except ValueError as exc:
            raise MikroTikError(
                f"routeros_invalid_json:{path}"
            ) from exc

    def _get_records(self, path: str) -> list[dict[str, Any]]:
        payload = self._request("GET", path)
        if isinstance(payload, dict):
            return [payload]
        if not isinstance(payload, list):
            raise MikroTikError(
                f"routeros_unexpected_response:{path}"
            )
        return [
            item
            for item in payload
            if isinstance(item, dict)
        ]

    def snapshot(self) -> MikroTikSnapshot:
        identity = _first_record(
            self._get_records("system/identity")
        )
        resource = _first_record(
            self._get_records("system/resource")
        )
        interfaces = self._get_records("interface")
        addresses = self._get_records("ip/address")
        routes = self._get_records("ip/route")
        dhcp_clients = self._get_records("ip/dhcp-client")
        dns = _first_record(self._get_records("ip/dns"))

        return MikroTikSnapshot(
            identity=identity,
            resource=resource,
            interfaces=interfaces,
            addresses=addresses,
            routes=routes,
            dhcp_clients=dhcp_clients,
            dns=dns,
        )

    def status(self) -> dict[str, Any]:
        snapshot = self.snapshot()
        default_routes = [
            route
            for route in snapshot.routes
            if route.get("dst-address") == "0.0.0.0/0"
            and route.get("disabled") != "true"
            and route.get("inactive") != "true"
        ]
        dhcp_states = [
            {
                "interface": row.get("interface"),
                "status": row.get("status"),
                "address": row.get("address"),
                "gateway": row.get("gateway"),
            }
            for row in snapshot.dhcp_clients
        ]

        return {
            "connected": True,
            "identity": snapshot.identity.get("name"),
            "version": snapshot.resource.get("version"),
            "uptime": snapshot.resource.get("uptime"),
            "cpu_load": snapshot.resource.get("cpu-load"),
            "free_memory": snapshot.resource.get("free-memory"),
            "default_route_present": bool(default_routes),
            "dhcp_clients": dhcp_states,
            "interface_count": len(snapshot.interfaces),
            "address_count": len(snapshot.addresses),
        }

    def renew_dhcp(self, interface: str) -> dict[str, Any]:
        clients = self._get_records("ip/dhcp-client")
        matching = [
            row
            for row in clients
            if row.get("interface") == interface
        ]

        if not matching:
            raise MikroTikError(
                "routeros_dhcp_client_not_found"
            )

        client_id = matching[0].get(".id")
        if not isinstance(client_id, str) or not client_id:
            raise MikroTikError(
                "routeros_dhcp_client_id_missing"
            )

        self._request(
            "POST",
            "ip/dhcp-client/renew",
            json={"numbers": client_id},
        )

        return {
            "action": "dhcp_renew",
            "interface": interface,
            "routeros_id": client_id,
        }
