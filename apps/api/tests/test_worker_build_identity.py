import importlib

import pytest


@pytest.mark.parametrize(
    "module_name",
    [
        "app.services.backup_scheduler_worker",
        "app.services.backup_alert_delivery_worker",
        (
            "app.services."
            "agent_lifecycle_alert_delivery_worker"
        ),
    ],
)
def test_worker_runs_build_identity_guard_before_loop(
    monkeypatch,
    module_name,
):
    module = importlib.import_module(module_name)
    calls = []

    class GuardCalled(RuntimeError):
        pass

    def fake_guard(settings):
        calls.append(settings)
        raise GuardCalled

    monkeypatch.setattr(
        module,
        "validate_production_build_identity",
        fake_guard,
    )

    with pytest.raises(GuardCalled):
        module.run_forever()

    assert len(calls) == 1
