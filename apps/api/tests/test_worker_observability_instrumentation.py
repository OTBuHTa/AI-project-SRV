import importlib

import pytest


WORKER_MODULES = (
    "app.services.backup_scheduler_worker",
    "app.services.backup_alert_delivery_worker",
    "app.services.agent_lifecycle_alert_delivery_worker",
)


class StopLoop(Exception):
    pass


@pytest.mark.parametrize(
    "module_name",
    WORKER_MODULES,
)
def test_worker_loop_records_success_processed_count(
    monkeypatch,
    module_name,
):
    module = importlib.import_module(module_name)

    events = []

    monkeypatch.setattr(
        module,
        "_record_started",
        lambda: events.append(("started", None)),
    )

    monkeypatch.setattr(
        module,
        "run_once",
        lambda: 7,
    )

    monkeypatch.setattr(
        module,
        "_record_succeeded",
        lambda processed: events.append(
            ("succeeded", processed)
        ),
    )

    monkeypatch.setattr(
        module,
        "_record_failed",
        lambda error: events.append(
            ("failed", error)
        ),
    )

    def stop_after_iteration(_seconds):
        raise StopLoop()

    monkeypatch.setattr(
        module.time,
        "sleep",
        stop_after_iteration,
    )

    with pytest.raises(StopLoop):
        module.run_forever()

    assert events == [
        ("started", None),
        ("succeeded", 7),
    ]


@pytest.mark.parametrize(
    "module_name",
    WORKER_MODULES,
)
def test_worker_loop_records_iteration_failure(
    monkeypatch,
    module_name,
):
    module = importlib.import_module(module_name)

    error = RuntimeError("iteration failed")
    events = []

    monkeypatch.setattr(
        module,
        "_record_started",
        lambda: events.append(("started", None)),
    )

    def fail_run_once():
        raise error

    monkeypatch.setattr(
        module,
        "run_once",
        fail_run_once,
    )

    monkeypatch.setattr(
        module,
        "_record_succeeded",
        lambda processed: events.append(
            ("succeeded", processed)
        ),
    )

    monkeypatch.setattr(
        module,
        "_record_failed",
        lambda observed_error: events.append(
            ("failed", observed_error)
        ),
    )

    def stop_after_iteration(_seconds):
        raise StopLoop()

    monkeypatch.setattr(
        module.time,
        "sleep",
        stop_after_iteration,
    )

    with pytest.raises(StopLoop):
        module.run_forever()

    assert events == [
        ("started", None),
        ("failed", error),
    ]


@pytest.mark.parametrize(
    "module_name",
    WORKER_MODULES,
)
def test_observability_write_failure_does_not_escape_worker(
    monkeypatch,
    module_name,
):
    module = importlib.import_module(module_name)

    def fail_write(**kwargs):
        raise RuntimeError("observability unavailable")

    monkeypatch.setattr(
        module,
        "persist_worker_started",
        fail_write,
    )
    monkeypatch.setattr(
        module,
        "persist_worker_succeeded",
        fail_write,
    )
    monkeypatch.setattr(
        module,
        "persist_worker_failed",
        fail_write,
    )

    module._record_started()
    module._record_succeeded(3)
    module._record_failed(
        RuntimeError("worker failure")
    )
