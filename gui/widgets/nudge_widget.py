from qtpy import QtCore
from qtpy.QtWidgets import (
    QWidget,
    QGridLayout,
    QToolButton,
    QSpinBox,
)
from gui.utils import send_message_to_server
from model.comm_protocol import Protocol
import typing

if typing.TYPE_CHECKING:
    from gui.websocket_client import WebSocketClient


class NudgeWidget(QWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
        websocket_client: "WebSocketClient | None" = None,
    ) -> None:
        super().__init__(parent)
        self.websocket_client = websocket_client
        nudge_buttons = QGridLayout()
        self.nudge_amount_spin_box = QSpinBox()
        self.nudge_amount_spin_box.setValue(10)
        self.nudge_amount_spin_box.setMaximum(5000)
        self.nudge_amount_spin_box.setMinimum(0)

        up_button = QToolButton()
        up_button.setArrowType(QtCore.Qt.ArrowType.UpArrow)
        up_button.clicked.connect(lambda: self.nudge("up"))
        down_button = QToolButton()
        down_button.setArrowType(QtCore.Qt.ArrowType.DownArrow)
        down_button.clicked.connect(lambda: self.nudge("down"))

        left_button = QToolButton()
        left_button.setArrowType(QtCore.Qt.ArrowType.LeftArrow)
        left_button.clicked.connect(lambda: self.nudge("left"))

        right_button = QToolButton()
        right_button.setArrowType(QtCore.Qt.ArrowType.RightArrow)
        right_button.clicked.connect(lambda: self.nudge("right"))

        nudge_buttons.addWidget(
            self.nudge_amount_spin_box, 1, 1, QtCore.Qt.AlignmentFlag.AlignCenter
        )
        nudge_buttons.addWidget(up_button, 0, 1, QtCore.Qt.AlignmentFlag.AlignCenter)
        nudge_buttons.addWidget(down_button, 2, 1, QtCore.Qt.AlignmentFlag.AlignCenter)
        nudge_buttons.addWidget(left_button, 1, 0, QtCore.Qt.AlignmentFlag.AlignCenter)
        nudge_buttons.addWidget(right_button, 1, 2, QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setLayout(nudge_buttons)

    def nudge(self, direction: str):
        if not self.websocket_client:
            return
        nudge_amount = self.nudge_amount_spin_box.value()
        delta_values = {
            "up": (0, nudge_amount),
            "down": (0, -nudge_amount),
            "left": (-nudge_amount, 0),
            "right": (nudge_amount, 0),
        }

        delta = delta_values.get(direction, (0, 0))
        send_message_to_server(
            self.websocket_client,
            {
                Protocol.Key.ACTION: Protocol.Action.NUDGE_GONIO,
                Protocol.Key.METADATA: {
                    Protocol.Key.X_DELTA: delta[0],
                    Protocol.Key.Y_DELTA: delta[1],
                },
            },
        )
