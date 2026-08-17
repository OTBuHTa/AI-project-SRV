from __future__ import annotations

import sys
from pathlib import Path

from app.version import API_VERSION


REPO_ROOT = Path(__file__).resolve().parents[3]


def verify_release_metadata(repo_root: Path, version: str = API_VERSION) -> int:
    errors: list[str] = []

    readme = repo_root / "README.md"
    release_note = repo_root / "docs" / f"RELEASE-v{version}.md"

    if not readme.is_file():
        errors.append(f"README not found: {readme}")
    else:
        lines = readme.read_text(encoding="utf-8").splitlines()
        marker = f"`v{version}`"
        milestone = next((lines[i + 1].strip() for i, line in enumerate(lines[:-1]) if line.strip() == "## Current milestone"), "")
        if marker not in milestone:
            errors.append(f"README current milestone does not reference {marker}")

    if not release_note.is_file():
        errors.append(f"release note not found: {release_note}")
    else:
        lines = release_note.read_text(encoding="utf-8").splitlines()
        expected_header = f"# v{version}"
        actual_header = lines[0].strip() if lines else ""
        if actual_header != expected_header:
            errors.append(
                f"{release_note}: expected header {expected_header!r}, "
                f"found {actual_header!r}"
            )

    if errors:
        print("Release metadata verification FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Verified release metadata for v{version}.")
    return 0


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else REPO_ROOT
    return verify_release_metadata(root)


if __name__ == "__main__":
    raise SystemExit(main())
