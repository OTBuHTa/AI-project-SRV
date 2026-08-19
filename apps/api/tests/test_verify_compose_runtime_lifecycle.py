from scripts import verify_compose_runtime_lifecycle as verifier


def _config():
    return {
        "services": {
            name: {
                "restart": policy,
            }
            for name, policy in (
                verifier.EXPECTED_RESTART_POLICIES.items()
            )
        }
    }


def test_accepts_expected_restart_policies(capsys):
    assert (
        verifier.verify_compose_runtime_lifecycle(
            _config()
        )
        == 0
    )

    output = capsys.readouterr().out
    assert (
        "Verified Compose runtime lifecycle restart "
        "policy for 7 services."
    ) in output


def test_rejects_missing_restart_policy(capsys):
    config = _config()
    config["services"]["api"].pop("restart")

    assert (
        verifier.verify_compose_runtime_lifecycle(
            config
        )
        == 1
    )

    output = capsys.readouterr().out
    assert "api: restart=None" in output


def test_rejects_wrong_restart_policy(capsys):
    config = _config()
    config["services"]["postgres"]["restart"] = "no"

    assert (
        verifier.verify_compose_runtime_lifecycle(
            config
        )
        == 1
    )

    output = capsys.readouterr().out
    assert "postgres: restart=" in output
    assert "expected=" in output


def test_rejects_missing_service(capsys):
    config = _config()
    del config["services"]["redis"]

    assert (
        verifier.verify_compose_runtime_lifecycle(
            config
        )
        == 1
    )

    output = capsys.readouterr().out
    assert (
        "redis: service definition is missing"
        in output
    )
