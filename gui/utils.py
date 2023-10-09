import asyncio
import getpass
from uuid import UUID

from qtpy.QtWidgets import QWidget

from model.comm_protocol import ExecuteRequest, Message, PayloadType, QueueRequest

from .websocket_client import WebSocketClient


def update_button_style(
    button: QWidget,
    size: int,
    selected=False,
    queued="not queued",
    exposed="not exposed",
) -> QWidget:
    # Define base style
    style = f"font-size: 14px; min-width: {size}px; min-height: {size}px;"
    base_color = "#ffffff"  # Base color for unselected state
    border_color = "#ffffff"  # Base border color for unselected state

    # Define colors for different states
    # https://rgbcolorcode.com
    state_colors = {
        "partially queued": "#ff8066",  # Salmon
        "queued": "#e62600",  # Ferrari red
        "partially exposed": "#fff7cc",  # Lemon chiffon
        "exposed": "#ffee99",  # Flavescent
    }

    # Based on queued state, update border color
    if queued in state_colors:
        border_color = state_colors[queued]

    # Based on exposed state, update base color
    if exposed in state_colors:
        base_color = state_colors[exposed]

    # If selected, darken the color by subtracting from RGB values
    if selected:
        base_color = "#" + "".join(
            [
                hex(max(0, int(base_color[i : i + 2], 16) - int("20", 16)))[2:].zfill(2)
                for i in range(1, 6, 2)
            ]
        )
        border_color = "#" + "".join(
            [
                hex(max(0, int(border_color[i : i + 2], 16) - int("20", 16)))[2:].zfill(
                    2
                )
                for i in range(1, 6, 2)
            ]
        )

    style += f"background-color: {base_color}; border: 3px solid {border_color};"
    button.setStyleSheet(style)
    return button


def send_message_to_server(client: WebSocketClient, message: Message):
    asyncio.run_coroutine_threadsafe(
        client.send(message.json()),
        client.loop,
    )


def create_execute_action_request(payload: PayloadType, client_id: UUID) -> Message:
    return Message(
        metadata=ExecuteRequest(user_id=getpass.getuser(), client_id=client_id),
        payload=payload,
    )


def create_add_to_queue_request(payload: PayloadType, client_id: UUID) -> Message:
    return Message(
        metadata=QueueRequest(user_id=getpass.getuser(), client_id=client_id),
        payload=payload,
    )
