import typing

from qtpy import QtCore
from qtpy.QtWidgets import QGridLayout, QSpinBox, QToolButton, QWidget

from gui.utils import create_execute_action_request, send_message_to_server
from model.comm_protocol import NudgeGonio

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

        self.focus_amount_spin_box = QSpinBox()
        self.focus_amount_spin_box.setValue(10)
        self.focus_amount_spin_box.setMaximum(100)
        self.focus_amount_spin_box.setMinimum(0)

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

        focus_in_button = QToolButton()
        focus_in_button.setText("+")
        focus_in_button.clicked.connect(lambda: self.nudge("in"))

        focus_out_button = QToolButton()
        focus_out_button.setText("-")
        focus_out_button.clicked.connect(lambda: self.nudge("out"))

        nudge_buttons.addWidget(
            self.nudge_amount_spin_box, 1, 1, QtCore.Qt.AlignmentFlag.AlignCenter
        )
        nudge_buttons.addWidget(up_button, 0, 1, QtCore.Qt.AlignmentFlag.AlignCenter)
        nudge_buttons.addWidget(down_button, 2, 1, QtCore.Qt.AlignmentFlag.AlignCenter)
        nudge_buttons.addWidget(left_button, 1, 0, QtCore.Qt.AlignmentFlag.AlignCenter)
        nudge_buttons.addWidget(right_button, 1, 2, QtCore.Qt.AlignmentFlag.AlignCenter)
        
        nudge_buttons.addWidget(focus_in_button, 0, 3, QtCore.Qt.AlignmentFlag.AlignCenter)
        nudge_buttons.addWidget(self.focus_amount_spin_box, 1, 3, QtCore.Qt.AlignmentFlag.AlignCenter)
        nudge_buttons.addWidget(focus_out_button, 2, 3, QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setLayout(nudge_buttons)

    def nudge(self, direction: str):
        if not self.websocket_client:
            return
        
        nudge_amount = self.nudge_amount_spin_box.value()
        if direction in ["in", "out"]:
            nudge_amount = self.focus_amount_spin_box.value()
        
        delta_values = {
            "up": (0, nudge_amount, 0),
            "down": (0, -nudge_amount, 0),
            "left": (-nudge_amount, 0, 0),
            "right": (nudge_amount, 0, 0),
            "in": (0, 0, nudge_amount),
            "out": (0, 0, -nudge_amount)
        }

        delta = delta_values.get(direction, (0, 0, 0))

        send_message_to_server(
            self.websocket_client,
            create_execute_action_request(
                NudgeGonio(x_delta=delta[0], y_delta=delta[1], z_delta=delta[2]),
                client_id=self.websocket_client.uuid,
            ),
        )
