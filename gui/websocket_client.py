import asyncio
import getpass
from uuid import uuid4

import websockets
from fastapi.exceptions import WebSocketRequestValidationError
from pydantic import parse_obj_as
from PyQt5.QtCore import QObject
from qtpy.QtCore import QThread, Signal  # type: ignore

from model.comm_protocol import Message


class WebSocketClient(QThread):
    message_received = Signal(object)

    def __init__(
        self, parent: QObject | None = None, server_url="localhost:8000"
    ) -> None:
        super().__init__(parent)
        self.server_url = server_url
        self.uuid = uuid4()

    async def connect(self):
        try:
            self.websocket = await websockets.connect(  # type: ignore
                f"ws://{self.server_url}/gui/ws/{self.uuid}/{getpass.getuser()}"
            )
            await self.listen()
        except ConnectionRefusedError:
            self.message_received.emit('{"error": "Connection refused"}')
        except WebSocketRequestValidationError:
            self.message_received.emit('{"error": "Connection could not be validated"}')
        except Exception as e:
            self.message_received.emit(f'{{"error": "Unknown error : {e}"}}')

    async def listen(self):
        while True:
            message = await self.websocket.recv()
            message = parse_obj_as(Message, message)
            self.message_received.emit(message)

    async def send(self, message):
        print(f"sending message: {message}")
        await self.websocket.send(message)

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.connect())
