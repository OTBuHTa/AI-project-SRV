import asyncio
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi import WebSocketDisconnect

import app.api.v1.monitoring as monitoring
from app.models.core import Role


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
        raise ValueError(
            "invalid websocket auth message"
        )

    async def close(
        self,
        code: int = 1000,
    ) -> None:
        self.close_code = code
        raise WebSocketDisconnect(code=1006)


class _AuthenticatedSocket:
    def __init__(self) -> None:
        self.accepted = False
        self.close_code: int | None = None
        self.messages: list[dict] = []

    async def accept(self) -> None:
        self.accepted = True

    async def receive_json(self):
        return {
            "type": "auth",
            "token": "access-token",
        }

    async def send_json(
        self,
        message: dict,
    ) -> None:
        self.messages.append(message)

    async def receive_text(self):
        raise WebSocketDisconnect(code=1000)

    async def close(
        self,
        code: int = 1000,
    ) -> None:
        self.close_code = code


class _FakeDb:
    def __init__(self, membership) -> None:
        self.membership = membership

    def scalar(self, statement):
        return self.membership


class _FakeSession:
    def __init__(self, membership) -> None:
        self.db = _FakeDb(membership)

    def __enter__(self):
        return self.db

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ) -> None:
        return None


def _configure_authenticated_session(
    monkeypatch,
    *,
    user_id: uuid.UUID,
    membership,
):
    monkeypatch.setattr(
        monitoring,
        "decode_access_token",
        lambda token: {
            "sub": str(user_id),
        },
    )

    monkeypatch.setattr(
        monitoring,
        "SessionLocal",
        lambda: _FakeSession(membership),
    )


def test_disconnect_before_auth_returns_cleanly():
    websocket = _DisconnectBeforeAuth()

    asyncio.run(
        monitoring.workspace_ws(
            websocket,
            uuid.uuid4(),
        )
    )

    assert websocket.accepted is True
    assert websocket.close_called is False


def test_auth_failure_tolerates_disconnect_during_close():
    websocket = _InvalidAuthDisconnectOnClose()

    asyncio.run(
        monitoring.workspace_ws(
            websocket,
            uuid.uuid4(),
        )
    )

    assert websocket.accepted is True
    assert websocket.close_code == 4401


def test_invalid_access_token_is_rejected(
    monkeypatch,
):
    websocket = _AuthenticatedSocket()

    def reject_token(token):
        raise ValueError("invalid token")

    monkeypatch.setattr(
        monitoring,
        "decode_access_token",
        reject_token,
    )

    monkeypatch.setattr(
        monitoring,
        "SessionLocal",
        lambda: (_ for _ in ()).throw(
            AssertionError(
                "database must not be accessed "
                "for an invalid token"
            )
        ),
    )

    asyncio.run(
        monitoring.workspace_ws(
            websocket,
            uuid.uuid4(),
        )
    )

    assert websocket.accepted is True
    assert websocket.close_code == 4401
    assert websocket.messages == []


def test_cross_workspace_membership_is_rejected(
    monkeypatch,
):
    user_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    websocket = _AuthenticatedSocket()

    _configure_authenticated_session(
        monkeypatch,
        user_id=user_id,
        membership=None,
    )

    register = AsyncMock()
    disconnect = AsyncMock()

    monkeypatch.setattr(
        monitoring.hub,
        "register",
        register,
    )

    monkeypatch.setattr(
        monitoring.hub,
        "disconnect",
        disconnect,
    )

    asyncio.run(
        monitoring.workspace_ws(
            websocket,
            workspace_id,
        )
    )

    assert websocket.close_code == 4403
    assert websocket.messages == []
    register.assert_not_awaited()
    disconnect.assert_not_awaited()


def test_member_without_resource_read_is_rejected(
    monkeypatch,
):
    user_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    websocket = _AuthenticatedSocket()

    membership = SimpleNamespace(
        role=Role.BILLING_MANAGER.value,
    )

    _configure_authenticated_session(
        monkeypatch,
        user_id=user_id,
        membership=membership,
    )

    register = AsyncMock()
    disconnect = AsyncMock()

    monkeypatch.setattr(
        monitoring.hub,
        "register",
        register,
    )

    monkeypatch.setattr(
        monitoring.hub,
        "disconnect",
        disconnect,
    )

    asyncio.run(
        monitoring.workspace_ws(
            websocket,
            workspace_id,
        )
    )

    assert websocket.close_code == 4403
    assert websocket.messages == []
    register.assert_not_awaited()
    disconnect.assert_not_awaited()


def test_member_with_resource_read_can_connect(
    monkeypatch,
):
    user_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    websocket = _AuthenticatedSocket()

    membership = SimpleNamespace(
        role=Role.VIEWER.value,
    )

    _configure_authenticated_session(
        monkeypatch,
        user_id=user_id,
        membership=membership,
    )

    register = AsyncMock()
    disconnect = AsyncMock()

    monkeypatch.setattr(
        monitoring.hub,
        "register",
        register,
    )

    monkeypatch.setattr(
        monitoring.hub,
        "disconnect",
        disconnect,
    )

    asyncio.run(
        monitoring.workspace_ws(
            websocket,
            workspace_id,
        )
    )

    assert websocket.accepted is True
    assert websocket.close_code is None
    assert websocket.messages == [
        {
            "type": "auth.ok",
        }
    ]

    register.assert_awaited_once_with(
        workspace_id,
        websocket,
    )

    disconnect.assert_awaited_once_with(
        workspace_id,
        websocket,
    )
