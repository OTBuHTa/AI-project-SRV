import asyncio
import json
from collections import defaultdict
from uuid import UUID
from fastapi import WebSocket

class RealtimeHub:
    def __init__(self):
        self._clients: dict[UUID, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, workspace_id: UUID, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self._clients[workspace_id].add(websocket)

    async def disconnect(self, workspace_id: UUID, websocket: WebSocket):
        async with self._lock:
            self._clients[workspace_id].discard(websocket)

    async def broadcast(self, workspace_id: UUID, event: dict):
        stale=[]
        payload=json.dumps(event, default=str)
        for ws in list(self._clients.get(workspace_id, set())):
            try:
                await ws.send_text(payload)
            except Exception:
                stale.append(ws)
        for ws in stale:
            self._clients[workspace_id].discard(ws)

hub = RealtimeHub()
