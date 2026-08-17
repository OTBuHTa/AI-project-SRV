from pathlib import Path

from scripts import verify_release_metadata as verifier


VERSION = "0.1.35-alpha"


def _write_repo(
    tmp_path: Path,
    *,
    milestone: str = VERSION,
    release_header: str | None = None,
) -> Path:
    readme = tmp_path / "README.md"
    readme.write_text(
        "# Project\n\n## Current milestone\n"
        f"`v{milestone}` — test baseline.\n",
        encoding="utf-8",
    )

    if release_header is not None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / f"RELEASE-v{VERSION}.md").write_text(
            f"{release_header}\n",
            encoding="utf-8",
        )

    return tmp_path


def test_verify_release_metadata_accepts_consistent_metadata(tmp_path, capsys):
    root = _write_repo(
        tmp_path,
        release_header=f"# v{VERSION}",
    )

    assert verifier.verify_release_metadata(root, VERSION) == 0
    assert (
        f"Verified release metadata for v{VERSION}."
        in capsys.readouterr().out
    )


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
