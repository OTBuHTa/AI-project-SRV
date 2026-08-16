from importlib import metadata
from pathlib import Path

from packaging.utils import canonicalize_name

from scripts import verify_ci_constraints as verifier


def _write_constraints(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "constraints.txt"
    path.write_text(content, encoding="utf-8")
    return path


def _fake_versions(versions: dict[str, str]):
    normalized = {
        canonicalize_name(name): version
        for name, version in versions.items()
    }

    def version(name: str) -> str:
        key = canonicalize_name(name)

        if key not in normalized:
            raise metadata.PackageNotFoundError(name)

        return normalized[key]

    return version


def test_verify_constraints_accepts_exact_installed_baseline(
    tmp_path,
    monkeypatch,
    capsys,
):
    path = _write_constraints(
        tmp_path,
        """
# comment

My_Pkg==1.0
beta==2.0
""",
    )

    monkeypatch.setattr(verifier, "EXPECTED_PIN_COUNT", 2)
    monkeypatch.setattr(
        verifier.metadata,
        "version",
        _fake_versions(
            {
                "my-pkg": "1.0",
                "beta": "2.0",
            }
        ),
    )

    assert verifier.verify_constraints(path) == 0

    output = capsys.readouterr().out
    assert "Verified 2 exact CI dependency constraint pins." in output


def test_verify_constraints_rejects_version_mismatch(
    tmp_path,
    monkeypatch,
    capsys,
):
    path = _write_constraints(tmp_path, "alpha==1.0\n")

    monkeypatch.setattr(verifier, "EXPECTED_PIN_COUNT", 1)
    monkeypatch.setattr(
        verifier.metadata,
        "version",
        _fake_versions({"alpha": "9.9"}),
    )

    assert verifier.verify_constraints(path) == 1

    output = capsys.readouterr().out
    assert "alpha: installed=9.9 expected=1.0" in output


def test_verify_constraints_rejects_uninstalled_package(
    tmp_path,
    monkeypatch,
    capsys,
):
    path = _write_constraints(tmp_path, "alpha==1.0\n")

    monkeypatch.setattr(verifier, "EXPECTED_PIN_COUNT", 1)
    monkeypatch.setattr(
        verifier.metadata,
        "version",
        _fake_versions({}),
    )

    assert verifier.verify_constraints(path) == 1

    output = capsys.readouterr().out
    assert "alpha: not installed; expected 1.0" in output


def test_verify_constraints_rejects_non_exact_pin(
    tmp_path,
    monkeypatch,
    capsys,
):
    path = _write_constraints(tmp_path, "alpha>=1.0\n")

    monkeypatch.setattr(verifier, "EXPECTED_PIN_COUNT", 1)

    assert verifier.verify_constraints(path) == 1

    output = capsys.readouterr().out
    assert "expected one exact == pin: alpha>=1.0" in output


def test_verify_constraints_rejects_duplicate_canonical_package(
    tmp_path,
    monkeypatch,
    capsys,
):
    path = _write_constraints(
        tmp_path,
        """
My_Pkg==1.0
my-pkg==1.0
""",
    )

    monkeypatch.setattr(verifier, "EXPECTED_PIN_COUNT", 2)
    monkeypatch.setattr(
        verifier.metadata,
        "version",
        _fake_versions({"my-pkg": "1.0"}),
    )

    assert verifier.verify_constraints(path) == 1

    output = capsys.readouterr().out
    assert "duplicate constraint for my-pkg" in output


def test_verify_constraints_rejects_incomplete_pin_count(
    tmp_path,
    monkeypatch,
    capsys,
):
    path = _write_constraints(tmp_path, "alpha==1.0\n")

    monkeypatch.setattr(verifier, "EXPECTED_PIN_COUNT", 2)
    monkeypatch.setattr(
        verifier.metadata,
        "version",
        _fake_versions({"alpha": "1.0"}),
    )

    assert verifier.verify_constraints(path) == 1

    output = capsys.readouterr().out
    assert "expected 2 exact constraint pins, found 1" in output
