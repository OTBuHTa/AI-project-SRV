from __future__ import annotations

import re
import sys
from pathlib import Path

from app.version import API_VERSION

REPO_ROOT = Path(__file__).resolve().parents[3]

VERSION_RE = re.compile(
    r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)-alpha$"
)
RELEASE_NOTE_RE = re.compile(
    r"^RELEASE-v(?P<version>\d+\.\d+\.\d+-alpha)\.md$"
)


def _version_key(version: str) -> tuple[int, int, int]:
    match = VERSION_RE.fullmatch(version)
    if match is None:
        raise ValueError(f"unsupported release version: {version}")

    return (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
    )


def _latest_release_version(repo_root: Path) -> str | None:
    docs = repo_root / "docs"
    if not docs.is_dir():
        return None

    versions: list[str] = []
    for path in docs.iterdir():
        match = RELEASE_NOTE_RE.fullmatch(path.name)
        if match is not None:
            versions.append(match.group("version"))

    if not versions:
        return None

    return max(versions, key=_version_key)


def verify_release_metadata(
    repo_root: Path,
    version: str = API_VERSION,
) -> int:
    errors: list[str] = []

    readme = repo_root / "README.md"
    release_note = repo_root / "docs" / f"RELEASE-v{version}.md"

    try:
        current_version_key = _version_key(version)
    except ValueError as exc:
        errors.append(str(exc))
        current_version_key = None

    if not readme.is_file():
        errors.append(f"README not found: {readme}")
    else:
        lines = readme.read_text(encoding="utf-8").splitlines()
        marker = f"`v{version}`"
        milestone = next(
            (
                lines[i + 1].strip()
                for i, line in enumerate(lines[:-1])
                if line.strip() == "## Current milestone"
            ),
            "",
        )
        if marker not in milestone:
            errors.append(
                f"README current milestone does not reference {marker}"
            )

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

    latest_release_version = _latest_release_version(repo_root)
    if (
        current_version_key is not None
        and latest_release_version is not None
        and current_version_key < _version_key(latest_release_version)
    ):
        errors.append(
            f"runtime version v{version} is older than latest release note "
            f"v{latest_release_version}"
        )

    if errors:
        print("Release metadata verification FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Verified release metadata for v{version}.")
    return 0


def main() -> int:
    root = (
        Path(sys.argv[1]).resolve()
        if len(sys.argv) > 1
        else REPO_ROOT
    )
    return verify_release_metadata(root)


if __name__ == "__main__":
    raise SystemExit(main())
