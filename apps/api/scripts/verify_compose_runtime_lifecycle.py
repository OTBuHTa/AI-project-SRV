from __future__ import annotations

import json
import sys
from collections.abc import Mapping


EXPECTED_RESTART_POLICIES = {
    "postgres": "unless-stopped",
    "redis": "unless-stopped",
    "api": "unless-stopped",
    "web": "unless-stopped",
    "backup-scheduler": "unless-stopped",
    "backup-alert-delivery": "unless-stopped",
    "agent-lifecycle-alert-delivery": "unless-stopped",
}


def verify_compose_runtime_lifecycle(
    config: Mapping[str, object],
) -> int:
    errors: list[str] = []

    services = config.get("services")

    if not isinstance(services, Mapping):
        errors.append(
            "Compose config does not contain a services mapping"
        )
    else:
        for service_name, expected_policy in (
            EXPECTED_RESTART_POLICIES.items()
        ):
            service = services.get(service_name)

            if not isinstance(service, Mapping):
                errors.append(
                    f"{service_name}: service definition is missing"
                )
                continue

            actual_policy = service.get("restart")

            if actual_policy != expected_policy:
                errors.append(
                    f"{service_name}: "
                    f"restart={actual_policy!r} "
                    f"expected={expected_policy!r}"
                )

    if errors:
        print(
            "Compose runtime lifecycle verification FAILED:"
        )
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        "Verified Compose runtime lifecycle restart "
        f"policy for {len(EXPECTED_RESTART_POLICIES)} "
        "services."
    )
    return 0


def main() -> int:
    try:
        config = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"invalid Compose JSON: {exc}")
        return 1

    if not isinstance(config, dict):
        print("Compose config root must be an object")
        return 1

    return verify_compose_runtime_lifecycle(config)


if __name__ == "__main__":
    raise SystemExit(main())
