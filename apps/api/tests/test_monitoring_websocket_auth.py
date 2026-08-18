import asyncio
import uuid

from fastapi import WebSocketDisconnect

from app.api.v1.monitoring import workspace_ws


class _DisconnectBeforeAuth:
    def __init__(self) -> None:
        self.accepted = False
        self.close_called = False

    async def accept(self) -> None:
        self.accepted = True

    async def receive_json(self):
        raise WebSocketDisconnect(code=1005)

    async def close(
        self,
        code: int = 1000,
    ) -> None:
        self.close_called = True
        raise AssertionError(
            "server must not close an already "
            "disconnected websocket"
        )


class _InvalidAuthDisconnectOnClose:
    def __init__(self) -> None:
        self.accepted = False
        self.close_code: int | None = None

    async def accept(self) -> None:
        self.accepted = True

    async def receive_json(self):
        raise ValueError("invalid websocket auth message")

    async def close(
        self,
        code: int = 1000,
    ) -> None:
        self.close_code = code
        raise WebSocketDisconnect(code=1006)


def test_disconnect_before_auth_returns_cleanly():
    websocket = _DisconnectBeforeAuth()

    asyncio.run(
        workspace_ws(
            websocket,
            uuid.uuid4(),
        )
    )

    assert websocket.accepted is True
    assert websocket.close_called is False


def test_auth_failure_tolerates_disconnect_during_close():
    websocket = _InvalidAuthDisconnectOnClose()

    asyncio.run(
        workspace_ws(
            websocket,
            uuid.uuid4(),
        )
    )

    assert websocket.accepted is True
    assert websocket.close_code == 4401
