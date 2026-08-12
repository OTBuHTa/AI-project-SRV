from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx

from ai_srv_agent.reliability import retry_http
from ai_srv_agent.state import save_state


ROTATION_WINDOW = timedelta(days=7)


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


def rotate_agent_token(
    state: dict,
    state_file: Path,
) -> bool:
    headers = {
        "Authorization":
            f"Bearer {state['agent_token']}",
    }

    def request() -> httpx.Response:
        response = httpx.post(
            (
                f"{state['api_url']}"
                "/api/v1/agents/token/rotate-self"
            ),
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()
        return response

    response = retry_http(request)
    payload = response.json()

    new_token = payload.get("agent_token")
    new_expiry = payload.get(
        "agent_token_expires_at"
    )

    if not new_token or not new_expiry:
        raise ValueError(
            "rotation response missing credentials"
        )

    updated_state = dict(state)
    updated_state["agent_token"] = new_token
    updated_state[
        "agent_token_expires_at"
    ] = new_expiry

    if payload.get("token_rotated_at"):
        updated_state[
            "token_rotated_at"
        ] = payload["token_rotated_at"]

    save_state(
        state_file,
        updated_state,
    )

    state.clear()
    state.update(updated_state)

    return True
