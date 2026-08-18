from scripts import verify_compose_build_identity as verifier


def _config(revision: str):
    return {
        "services": {
            name: {
                "build": {
                    "args": {
                        "APP_BUILD_REVISION": revision,
                    }
                }
            }
            for name in verifier.EXPECTED_SERVICES
        }
    }


def test_accepts_matching_revision(capsys):
    revision = (
        "0123456789abcdef0123456789abcdef01234567"
    )

    assert (
        verifier.verify_compose_build_identity(
            _config(revision),
            revision,
        )
        == 0
    )

    output = capsys.readouterr().out
    assert (
        "Verified Compose build identity wiring for "
        "4 services"
    ) in output


def test_rejects_mismatched_revision(capsys):
    config = _config("unknown")
    expected = (
        "0123456789abcdef0123456789abcdef01234567"
    )

    assert (
        verifier.verify_compose_build_identity(
            config,
            expected,
        )
        == 1
    )

    output = capsys.readouterr().out
    assert "APP_BUILD_REVISION=" in output
    assert "expected=" in output


def test_rejects_missing_service(capsys):
    config = _config("unknown")
    del config["services"]["backup-scheduler"]

    assert (
        verifier.verify_compose_build_identity(
            config,
            "unknown",
        )
        == 1
    )

    output = capsys.readouterr().out
    assert (
        "backup-scheduler: service definition is missing"
        in output
    )


def test_rejects_missing_build_args(capsys):
    config = _config("unknown")
    config["services"]["api"]["build"].pop("args")

    assert (
        verifier.verify_compose_build_identity(
            config,
            "unknown",
        )
        == 1
    )

    output = capsys.readouterr().out
    assert "api: build args are missing" in output
