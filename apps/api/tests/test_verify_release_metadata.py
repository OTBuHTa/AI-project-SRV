from pathlib import Path

from scripts import verify_release_metadata as verifier

VERSION = "0.1.35-alpha"


def _write_repo(
    tmp_path: Path,
    *,
    version: str = VERSION,
    milestone: str | None = None,
    release_header: str | None = None,
    package_version: str | None = None,
    extra_release_versions: tuple[str, ...] = (),
    extra_release_headers: tuple[tuple[str, str], ...] = (),
) -> Path:
    if milestone is None:
        milestone = version

    if package_version is None:
        package_version = (
            verifier._package_version_for_release(
                version
            )
        )

    api_dir = tmp_path / "apps" / "api"
    api_dir.mkdir(parents=True)

    (api_dir / "pyproject.toml").write_text(
        "[project]\n"
        'name = "test-api"\n'
        f'version = "{package_version}"\n',
        encoding="utf-8",
    )

    readme = tmp_path / "README.md"
    readme.write_text(
        "# Project\n\n## Current milestone\n"
        f"`v{milestone}` — test baseline.\n",
        encoding="utf-8",
    )

    docs = tmp_path / "docs"
    docs.mkdir()

    if release_header is not None:
        (docs / f"RELEASE-v{version}.md").write_text(
            f"{release_header}\n",
            encoding="utf-8",
        )

    for extra_version in extra_release_versions:
        (docs / f"RELEASE-v{extra_version}.md").write_text(
            f"# v{extra_version}\n",
            encoding="utf-8",
        )

    for extra_version, header in extra_release_headers:
        (docs / f"RELEASE-v{extra_version}.md").write_text(
            f"{header}\n",
            encoding="utf-8",
        )

    return tmp_path


def test_verify_release_metadata_accepts_consistent_metadata(
    tmp_path,
    capsys,
):
    root = _write_repo(
        tmp_path,
        release_header=f"# v{VERSION}",
    )

    assert verifier.verify_release_metadata(root, VERSION) == 0
    assert (
        f"Verified release metadata for v{VERSION}."
        in capsys.readouterr().out
    )


def test_verify_release_metadata_rejects_package_version_mismatch(
    tmp_path,
    capsys,
):
    root = _write_repo(
        tmp_path,
        release_header=f"# v{VERSION}",
        package_version="0.1.34a0",
    )

    assert verifier.verify_release_metadata(root, VERSION) == 1

    output = capsys.readouterr().out

    assert (
        "project.version '0.1.34a0' does not match "
        "runtime version v0.1.35-alpha"
        in output
    )
    assert "expected '0.1.35a0'" in output


def test_verify_release_metadata_rejects_stale_current_milestone(
    tmp_path,
    capsys,
):
    root = _write_repo(
        tmp_path,
        milestone="0.1.34-alpha",
        release_header=f"# v{VERSION}",
    )
    with (root / "README.md").open("a", encoding="utf-8") as stream:
        stream.write(f"\nHistory: `v{VERSION}`\n")

    assert verifier.verify_release_metadata(root, VERSION) == 1
    assert (
        f"README current milestone does not reference `v{VERSION}`"
        in capsys.readouterr().out
    )


def test_verify_release_metadata_rejects_missing_release_note(
    tmp_path,
    capsys,
):
    root = _write_repo(tmp_path)

    assert verifier.verify_release_metadata(root, VERSION) == 1
    assert "release note not found:" in capsys.readouterr().out


def test_verify_release_metadata_rejects_wrong_release_header(
    tmp_path,
    capsys,
):
    root = _write_repo(
        tmp_path,
        release_header="# v0.1.34-alpha",
    )

    assert verifier.verify_release_metadata(root, VERSION) == 1
    output = capsys.readouterr().out
    assert f"expected header '# v{VERSION}'" in output
    assert "found '# v0.1.34-alpha'" in output


def test_verify_release_metadata_rejects_version_regression(
    tmp_path,
    capsys,
):
    root = _write_repo(
        tmp_path,
        release_header=f"# v{VERSION}",
        extra_release_versions=("0.1.36-alpha",),
    )

    assert verifier.verify_release_metadata(root, VERSION) == 1
    assert (
        "runtime version v0.1.35-alpha is older than latest release note "
        "v0.1.36-alpha"
        in capsys.readouterr().out
    )


def test_release_version_order_is_numeric(
    tmp_path,
    capsys,
):
    version = "0.1.9-alpha"
    root = _write_repo(
        tmp_path,
        version=version,
        release_header=f"# v{version}",
        extra_release_versions=("0.1.10-alpha",),
    )

    assert verifier.verify_release_metadata(root, version) == 1
    assert (
        "runtime version v0.1.9-alpha is older than latest release note "
        "v0.1.10-alpha"
        in capsys.readouterr().out
    )


def test_verify_release_metadata_accepts_legacy_historical_headers(
    tmp_path,
    capsys,
):
    root = _write_repo(
        tmp_path,
        release_header=f"# v{VERSION}",
        extra_release_headers=(
            (
                "0.1.34-alpha",
                "# AI-project SRV v0.1.34-alpha",
            ),
            (
                "0.1.33-alpha",
                "# Release v0.1.33-alpha",
            ),
        ),
    )

    assert verifier.verify_release_metadata(root, VERSION) == 0
    assert (
        f"Verified release metadata for v{VERSION}."
        in capsys.readouterr().out
    )


def test_verify_release_metadata_rejects_historical_header_mismatch(
    tmp_path,
    capsys,
):
    root = _write_repo(
        tmp_path,
        release_header=f"# v{VERSION}",
        extra_release_headers=(
            (
                "0.1.34-alpha",
                "# AI-project SRV v0.1.33-alpha",
            ),
        ),
    )

    assert verifier.verify_release_metadata(root, VERSION) == 1
    output = capsys.readouterr().out
    assert (
        "historical release header does not match filename version "
        "v0.1.34-alpha"
        in output
    )
    assert "found '# AI-project SRV v0.1.33-alpha'" in output
