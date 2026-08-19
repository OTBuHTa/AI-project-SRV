from __future__ import annotations

import json

from app.services.mikrotik import MikroTikError, MikroTikClient


def main() -> int:
    try:
        with MikroTikClient() as client:
            status = client.status()
    except MikroTikError as exc:
        print(
            json.dumps(
                {
                    "result": "FAIL",
                    "error": str(exc),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    failures: list[str] = []

    if not status.get("default_route_present"):
        failures.append("default_route_missing")
    if not status.get("wan_running"):
        failures.append("wan_interface_not_running")
    if not status.get("wan_dhcp_bound"):
        failures.append("wan_dhcp_not_bound")
    if status.get("wan_ip_matches_expected") is False:
        failures.append("wan_ip_mismatch")

    output = {
        "result": "FAIL" if failures else "PASS",
        "failures": failures,
        "router": {
            "identity": status.get("identity"),
            "version": status.get("version"),
            "uptime": status.get("uptime"),
        },
        "wan": {
            "interface": status.get("wan_interface"),
            "running": status.get("wan_running"),
            "dhcp_bound": status.get("wan_dhcp_bound"),
            "address": status.get("wan_address"),
            "expected_address": status.get("expected_wan_ip"),
            "matches_expected": status.get(
                "wan_ip_matches_expected"
            ),
        },
    }
    print(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
