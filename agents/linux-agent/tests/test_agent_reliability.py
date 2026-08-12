import logging
from unittest.mock import MagicMock, patch

import httpx

from ai_srv_agent.main import heartbeat, poll_and_execute_task, run_cycle


def test_heartbeat_retries_temporary_api_failure():
    state = {
        "api_url": "https://example.test",
        "agent_id": "agent-id",
        "agent_token": "secret-token",
    }
    response = MagicMock()

    with (
        patch("ai_srv_agent.main.collect_metrics", return_value={}),
        patch("ai_srv_agent.main.collect_docker", return_value={}),
        patch(
            "ai_srv_agent.main.httpx.post",
            side_effect=[httpx.ConnectError("offline"), response],
        ) as post,
        patch("ai_srv_agent.reliability.time.sleep"),
    ):
        heartbeat(state)

    assert post.call_count == 2
    response.raise_for_status.assert_called_once()


def test_task_polling_retries_temporary_api_failure():
    state = {
        "api_url": "https://example.test",
        "agent_id": "agent-id",
        "agent_token": "secret-token",
    }
    response = MagicMock()
    response.json.return_value = None

    with (
        patch(
            "ai_srv_agent.main.httpx.get",
            side_effect=[httpx.ReadTimeout("slow"), response],
        ) as get,
        patch("ai_srv_agent.reliability.time.sleep"),
    ):
        poll_and_execute_task(state)

    assert get.call_count == 2


def test_run_cycle_continues_after_temporary_failure(caplog):
    state = {}
    failure = httpx.ConnectError("offline")

    with (
        patch("ai_srv_agent.main.heartbeat", side_effect=failure),
        patch("ai_srv_agent.main.submit_inventory") as inventory,
        patch("ai_srv_agent.main.poll_and_execute_task") as task_polling,
        caplog.at_level(logging.WARNING),
    ):
        run_cycle(state)

    inventory.assert_called_once_with(state)
    task_polling.assert_called_once_with(state)
    assert "agent will retry next cycle" in caplog.text
