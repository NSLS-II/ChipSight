from typing import Any
from uuid import UUID

from fastapi import WebSocket

from model.comm_protocol import Message


class ConnectionManager:
    """
    Keeps track of active connections
    """

    def __init__(self):
        self.active_connections: dict[UUID, WebSocket] = {}
        self.user_info: dict[UUID, dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, client_id: UUID):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.user_info[client_id] = {}

    def disconnect(self, client_id: UUID):
        self.active_connections.pop(client_id, None)
        self.user_info.pop(client_id, None)

    async def unicast(self, message: Message, client_id: UUID):
        websocket = self.active_connections.get(client_id, None)
        if websocket:
            await websocket.send_json(message.dict())

    async def broadcast(self, message: Message):
        for client_id, connection in self.active_connections.items():
            await connection.send_json(message.dict())
