from typing import Any
from fastapi import WebSocket


class ConnectionManager:
    """
    Keeps track of active connections
    """

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        print(message)
        data = {"message": message}
        await websocket.send_json(data)

    async def broadcast(self, message: "str | dict[str, Any]"):
        data = {"broadcast": message}
        for connection in self.active_connections:
            await connection.send_json(data)
