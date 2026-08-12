from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx

from ai_srv_agent.reliability import retry_http
from ai_srv_agent.state import save_state


ROTATION_WINDOW = timedelta(days=7)

_PENDING_TOKEN_KEY = "pending_agent_token"
_PENDING_EXPIRY_KEY = "pending_agent_token_expires_at"
_PENDING_PREPARED_KEY = "token_rotation_prepared_at"


def _parse_expiry(value: str) -> datetime:
    parsed = datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)

    return parsed.astimezone(UTC)


def token_needs_rotation(
    state: dict,
    *,
    now: datetime | None = None,
) -> bool:
    expires_at = state.get(
        "agent_token_expires_at"
    )

    if not expires_at:
        return False

    current_time = (
        now.astimezone(UTC)
        if now is not None
        else datetime.now(UTC)
    )

    token_expiry = _parse_expiry(
        str(expires_at)
    )

    return (
        token_expiry - current_time
        <= ROTATION_WINDOW
    )


def has_pending_agent_token(
    state: dict,
) -> bool:
    return bool(state.get(_PENDING_TOKEN_KEY))


def _authorization_headers(
    token: str,
) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
    }


def _clear_pending_fields(
    state: dict,
) -> dict:
    updated_state = dict(state)

    updated_state.pop(
        _PENDING_TOKEN_KEY,
        None,
    )
    updated_state.pop(
        _PENDING_EXPIRY_KEY,
        None,
    )
    updated_state.pop(
        _PENDING_PREPARED_KEY,
        None,
    )

    return updated_state


def _status_detail(
    exc: httpx.HTTPStatusError,
) -> str | None:
    try:
        payload = exc.response.json()
    except ValueError:
        return None

    if not isinstance(payload, dict):
        return None

    detail = payload.get("detail")

    return (
        str(detail)
        if detail is not None
        else None
    )


def prepare_agent_token_rotation(
    state: dict,
    state_file: Path,
) -> bool:
    headers = _authorization_headers(
        state["agent_token"]
    )

    def request() -> httpx.Response:
        response = httpx.post(
            (
                f"{state['api_url']}"
                "/api/v1/agents/"
                "token/rotate-self/prepare"
            ),
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()
        return response

    response = retry_http(request)
    payload = response.json()

    pending_token = payload.get(
        "pending_agent_token"
    )
    pending_expiry = payload.get(
        "pending_agent_token_expires_at"
    )
    prepared_at = payload.get(
        "token_rotation_prepared_at"
    )

    if (
        not pending_token
        or not pending_expiry
        or not prepared_at
    ):
        raise ValueError(
            "rotation prepare response "
            "missing credentials"
        )

    updated_state = dict(state)
    updated_state[
        _PENDING_TOKEN_KEY
    ] = pending_token
    updated_state[
        _PENDING_EXPIRY_KEY
    ] = pending_expiry
    updated_state[
        _PENDING_PREPARED_KEY
    ] = prepared_at

    # Critical ordering:
    # persist the pending credential before commit.
    save_state(
        state_file,
        updated_state,
    )

    state.clear()
    state.update(updated_state)

    return True


def commit_pending_agent_token_rotation(
    state: dict,
    state_file: Path,
) -> bool:
    pending_token = state.get(
        _PENDING_TOKEN_KEY
    )

    if not pending_token:
        return False

    headers = _authorization_headers(
        str(pending_token)
    )

    def request() -> httpx.Response:
        response = httpx.post(
            (
                f"{state['api_url']}"
                "/api/v1/agents/"
                "token/rotate-self/commit"
            ),
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()
        return response

    try:
        response = retry_http(request)
    except httpx.HTTPStatusError as exc:
        detail = _status_detail(exc)

        if detail in {
            "rotation_prepare_expired",
            "invalid_pending_agent_token",
        }:
            # The server did not accept this pending
            # credential. The active credential has
            # not been replaced by this failed commit,
            # so clear stale local pending state.
            updated_state = _clear_pending_fields(
                state
            )

            save_state(
                state_file,
                updated_state,
            )

            state.clear()
            state.update(updated_state)

        raise

    payload = response.json()

    token_expiry = payload.get(
        "agent_token_expires_at"
    )
    rotated_at = payload.get(
        "token_rotated_at"
    )

    if not token_expiry or not rotated_at:
        raise ValueError(
            "rotation commit response "
            "missing token metadata"
        )

    promoted_state = _clear_pending_fields(
        state
    )
    promoted_state["agent_token"] = (
        str(pending_token)
    )
    promoted_state[
        "agent_token_expires_at"
    ] = token_expiry
    promoted_state[
        "token_rotated_at"
    ] = rotated_at

    # Update memory first after a successful server
    # commit. If the final disk write fails, this
    # running process still uses the valid token.
    state.clear()
    state.update(promoted_state)

    # Disk previously contains both old + pending
    # credentials, so a crash here remains recoverable.
    save_state(
        state_file,
        promoted_state,
    )

    return True


def recover_pending_agent_token(
    state: dict,
    state_file: Path,
) -> bool:
    if not has_pending_agent_token(state):
        return False

    return commit_pending_agent_token_rotation(
        state,
        state_file,
    )


def rotate_agent_token(
    state: dict,
    state_file: Path,
) -> bool:
    if has_pending_agent_token(state):
        return recover_pending_agent_token(
            state,
            state_file,
        )

    prepare_agent_token_rotation(
        state,
        state_file,
    )

    return commit_pending_agent_token_rotation(
        state,
        state_file,
    )
