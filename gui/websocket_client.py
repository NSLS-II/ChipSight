import asyncio
import typing
import os
import getpass
from PyQt5.QtCore import QObject
import websockets
from qtpy.QtCore import QThread, Signal
from fastapi.exceptions import WebSocketRequestValidationError


class WebSocketClient(QThread):
    message_received = Signal(str)

    def __init__(
        self, parent: QObject | None = None, server_url="localhost", server_port=8000
    ) -> None:
        super().__init__(parent)
        self.server_url = server_url
        self.server_port = server_port

    async def connect(self):
        try:
            self.websocket = await websockets.connect(
                f"ws://{self.server_url}:{self.server_port}/ws/{os.getpid()}/{getpass.getuser()}"
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
            self.message_received.emit(message)

    async def send(self, message):
        print(f"sending message: {message}")
        await self.websocket.send(message)

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.connect())
