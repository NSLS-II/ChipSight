from qtpy import QtCore
from qtpy.QtWidgets import (
    QWidget,
    QGridLayout,
    QPushButton,
)
from gui.utils import send_message_to_server
from model.comm_protocol import Protocol
from .nudge_widget import NudgeWidget
import typing

if typing.TYPE_CHECKING:
    from gui.websocket_client import WebSocketClient


class ControlPanelWidget(QWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
        websocket_client: "WebSocketClient | None" = None,
    ) -> None:
        super().__init__(parent)
        self.websocket_client = websocket_client
        fidu_buttons = QGridLayout()

        F0_button = QPushButton("F0")
        F0_button.clicked.connect(lambda: self.go_to_fiducial("F0"))
        set_F0_button = QPushButton("Set F0")
        set_F0_button.clicked.connect(lambda: self.set_fiducial("F0"))

        F1_button = QPushButton("F1")
        F1_button.clicked.connect(lambda: self.go_to_fiducial("F1"))
        set_F1_button = QPushButton("Set F1")
        set_F1_button.clicked.connect(lambda: self.set_fiducial("F1"))

        F2_button = QPushButton("F2")
        F2_button.clicked.connect(lambda: self.go_to_fiducial("F2"))
        set_F2_button = QPushButton("Set F2")
        set_F2_button.clicked.connect(lambda: self.set_fiducial("F2"))

        fidu_buttons.addWidget(F0_button, 0, 1)
        fidu_buttons.addWidget(set_F0_button, 0, 2)
        fidu_buttons.addWidget(F1_button, 1, 1)
        fidu_buttons.addWidget(set_F1_button, 1, 2)
        fidu_buttons.addWidget(F2_button, 2, 1)
        fidu_buttons.addWidget(set_F2_button, 2, 2)
        nudge_widget = NudgeWidget(parent=self, websocket_client=self.websocket_client)
        fidu_buttons.addWidget(nudge_widget, 0, 0, 3, 1)
        self.setLayout(fidu_buttons)

    def go_to_fiducial(self, fiducial: str):
        if not self.websocket_client:
            return
        send_message_to_server(
            self.websocket_client,
            {
                Protocol.Key.ACTION: Protocol.Action.GO_TO_FIDUCIAL,
                Protocol.Key.METADATA: {Protocol.Key.NAME: fiducial},
            },
        )

    def set_fiducial(self, fiducial: str):
        if not self.websocket_client:
            return
        send_message_to_server(
            self.websocket_client,
            {
                Protocol.Key.ACTION: Protocol.Action.SET_FIDUCIAL,
                Protocol.Key.METADATA: {Protocol.Key.NAME: fiducial},
            },
        )
