from __future__ import annotations

import sys
from importlib import metadata
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


DEFAULT_CONSTRAINTS = Path("constraints/ci-py312-linux.txt")
EXPECTED_PIN_COUNT = 49


def verify_constraints(path: Path) -> int:
    checked = 0
    exact_pins = 0
    seen: set[str] = set()
    errors: list[str] = []

    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        try:
            requirement = Requirement(line)
        except Exception as exc:
            errors.append(
                f"{path}:{line_number}: invalid requirement: {exc}"
            )
            continue

        name = canonicalize_name(requirement.name)

        if name in seen:
            errors.append(
                f"{path}:{line_number}: duplicate constraint for "
                f"{requirement.name}"
            )
            continue

        seen.add(name)

        specifiers = list(requirement.specifier)

        if (
            len(specifiers) != 1
            or specifiers[0].operator != "=="
            or "*" in specifiers[0].version
        ):
            errors.append(
                f"{path}:{line_number}: expected one exact == pin: {line}"
            )
            continue

        exact_pins += 1
        expected = specifiers[0].version

        try:
            actual = metadata.version(requirement.name)
        except metadata.PackageNotFoundError:
            errors.append(
                f"{requirement.name}: not installed; expected {expected}"
            )
            continue

        checked += 1

        if actual != expected:
            errors.append(
                f"{requirement.name}: installed={actual} expected={expected}"
            )

    if exact_pins != EXPECTED_PIN_COUNT:
        errors.append(
            f"{path}: expected {EXPECTED_PIN_COUNT} exact constraint pins, "
            f"found {exact_pins}"
        )

    if checked == 0:
        errors.append(f"{path}: no installed exact constraint pins verified")

    if errors:
        print("CI dependency baseline verification FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Verified {checked} exact CI dependency constraint pins.")
    return 0


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CONSTRAINTS

    if not path.is_file():
        print(f"constraint file not found: {path}")
        return 1

    return verify_constraints(path)


if __name__ == "__main__":
    raise SystemExit(main())
