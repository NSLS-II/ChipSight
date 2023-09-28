from typing import Any
from fastapi import WebSocket


class ConnectionManager:
    """
    Keeps track of active connections
    """

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.user_info: dict[str, dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.user_info[client_id] = {}

    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)
        self.user_info.pop(client_id, None)

    async def unicast(self, message: "str | dict[str, Any]", client_id: str):
        data = {"unicast": message}
        websocket = self.active_connections.get(client_id, None)
        if websocket:
            await websocket.send_json(data)

    async def broadcast(self, message: "str | dict[str, Any]"):
        data = {"broadcast": message}
        for client_id, connection in self.active_connections.items():
            await connection.send_json(data)
