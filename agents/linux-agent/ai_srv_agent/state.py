import json
import os
import tempfile
from pathlib import Path


def load_state(state_file: Path) -> dict:
    state = json.loads(state_file.read_text(encoding="utf-8"))
    required = {"api_url", "agent_id", "agent_token"}
    missing = required.difference(state)
    if missing:
        raise ValueError(
            "Agent state is missing required fields: " + ", ".join(sorted(missing))
        )
    _restrict_permissions(state_file)
    return state


def save_state(state_file: Path, state: dict) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=state_file.parent,
            prefix=f".{state_file.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            _restrict_permissions(temporary_path)
            json.dump(state, temporary_file, indent=2)
            temporary_file.write("\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        os.replace(temporary_path, state_file)
        temporary_path = None
        _restrict_permissions(state_file)
        _sync_directory(state_file.parent)
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


def _restrict_permissions(path: Path) -> None:
    try:
        path.chmod(0o600)
    except OSError:
        pass


def _sync_directory(directory: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
