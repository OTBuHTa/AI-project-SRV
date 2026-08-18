from __future__ import annotations

import json
import sys
from collections.abc import Mapping


EXPECTED_SERVICES = (
    "api",
    "backup-scheduler",
    "backup-alert-delivery",
    "agent-lifecycle-alert-delivery",
)


def verify_compose_build_identity(
    config: Mapping[str, object],
    expected_revision: str,
) -> int:
    errors: list[str] = []

    services = config.get("services")

    if not isinstance(services, Mapping):
        errors.append("Compose config does not contain a services mapping")
    else:
        for service_name in EXPECTED_SERVICES:
            service = services.get(service_name)

            if not isinstance(service, Mapping):
                errors.append(
                    f"{service_name}: service definition is missing"
                )
                continue

            build = service.get("build")

            if not isinstance(build, Mapping):
                errors.append(
                    f"{service_name}: build definition is missing"
                )
                continue

            args = build.get("args")

            if not isinstance(args, Mapping):
                errors.append(
                    f"{service_name}: build args are missing"
                )
                continue

            actual_revision = args.get(
                "APP_BUILD_REVISION"
            )

            if actual_revision != expected_revision:
                errors.append(
                    f"{service_name}: "
                    f"APP_BUILD_REVISION={actual_revision!r} "
                    f"expected={expected_revision!r}"
                )

    if errors:
        print("Compose build identity verification FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        "Verified Compose build identity wiring for "
        f"{len(EXPECTED_SERVICES)} services: "
        f"{expected_revision}."
    )
    return 0


def main() -> int:
    if len(sys.argv) != 2:
        print(
            "usage: verify_compose_build_identity.py "
            "<expected-revision>"
        )
        return 2

    expected_revision = sys.argv[1]

    try:
        config = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"invalid Compose JSON: {exc}")
        return 1

    if not isinstance(config, dict):
        print("Compose config root must be an object")
        return 1

    return verify_compose_build_identity(
        config,
        expected_revision,
    )


if __name__ == "__main__":
    raise SystemExit(main())
