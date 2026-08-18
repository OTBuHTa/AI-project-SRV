#!/usr/bin/env python3
from pathlib import Path
import os
import sys


ROOT = Path(__file__).resolve().parents[1]

PROJECT_PYTHON = ROOT / ".venv" / "bin" / "python"

if (
    PROJECT_PYTHON.is_file()
    and Path(sys.executable).resolve()
    != PROJECT_PYTHON.resolve()
):
    os.execv(
        str(PROJECT_PYTHON),
        [
            str(PROJECT_PYTHON),
            str(Path(__file__).resolve()),
            *sys.argv[1:],
        ],
    )

sys.path.insert(
    0,
    str(ROOT / "apps" / "api"),
)

from app.core.production_preflight import (  # noqa: E402
    validate_production_env_file,
)


def main() -> int:
    if len(sys.argv) != 2:
        print(
            "usage: production-preflight.py "
            "<environment-file>",
            file=sys.stderr,
        )
        return 2

    env_path = Path(sys.argv[1])

    try:
        validate_production_env_file(
            env_path,
        )
    except Exception as exc:
        print(
            f"FAIL: {exc}",
            file=sys.stderr,
        )
        return 1

    print(
        "OK: production security preflight "
        f"passed for {env_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
