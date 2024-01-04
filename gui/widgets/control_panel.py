import typing

from qtpy.QtWidgets import QGridLayout, QPushButton, QWidget

from gui.utils import create_execute_action_request, send_message_to_server
from model.comm_protocol import GoToFiducial, SetFiducial, ClearFiducials

from .nudge_widget import NudgeWidget
from .misc import LedIndicator
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

        self.F0_button = QPushButton("Go to F0")
        self.F0_button.clicked.connect(lambda: self.go_to_fiducial("F0"))
        self.set_F0_button = QPushButton("Set F0")
        self.set_F0_button.clicked.connect(lambda: self.set_fiducial("F0"))
        self.F0_set_light = LedIndicator(self)

        self.F1_button = QPushButton("Go to F1")
        self.F1_button.clicked.connect(lambda: self.go_to_fiducial("F1"))
        self.set_F1_button = QPushButton("Set F1")
        self.set_F1_button.clicked.connect(lambda: self.set_fiducial("F1"))
        self.F1_set_light = LedIndicator(self)

        self.F2_button = QPushButton("Go to F2")
        self.F2_button.clicked.connect(lambda: self.go_to_fiducial("F2"))
        self.set_F2_button = QPushButton("Set F2")
        self.set_F2_button.clicked.connect(lambda: self.set_fiducial("F2"))
        self.F2_set_light = LedIndicator(self)

        self.clear_fidu_button = QPushButton("Clear Fiducials")
        self.clear_fidu_button.clicked.connect(self.clear_fiducials)

        fidu_buttons.addWidget(self.F0_button, 0, 1)
        fidu_buttons.addWidget(self.set_F0_button, 0, 2)
        fidu_buttons.addWidget(self.F0_set_light, 0, 3)
        fidu_buttons.addWidget(self.F1_button, 1, 1)
        fidu_buttons.addWidget(self.set_F1_button, 1, 2)
        fidu_buttons.addWidget(self.F1_set_light, 1, 3)
        fidu_buttons.addWidget(self.F2_button, 2, 1)
        fidu_buttons.addWidget(self.set_F2_button, 2, 2)
        fidu_buttons.addWidget(self.F2_set_light, 2, 3)
        fidu_buttons.addWidget(self.clear_fidu_button, 3, 1, 2, 1)

        nudge_widget = NudgeWidget(parent=self, websocket_client=self.websocket_client)
        fidu_buttons.addWidget(nudge_widget, 0, 0, 3, 1)
        self.setLayout(fidu_buttons)

    def go_to_fiducial(self, fiducial: str):
        for button in [self.F0_button, self.F1_button, self.F2_button]:
            button.setStyleSheet("")
        button = getattr(self, f"{fiducial}_button")
        button.setStyleSheet("border: 2px solid green;")
        if not self.websocket_client:
            return
        send_message_to_server(
            self.websocket_client,
            create_execute_action_request(
                GoToFiducial(name=fiducial), client_id=self.websocket_client.uuid
            ),
        )

    def set_fiducial(self, fiducial: str):
        for button in [self.set_F0_button, self.set_F1_button, self.set_F2_button]:
            button.setStyleSheet("")
        button = getattr(self, f"set_{fiducial}_button")
        button.setStyleSheet("border: 2px solid green;")
        if not self.websocket_client:
            return
        send_message_to_server(
            self.websocket_client,
            create_execute_action_request(
                SetFiducial(name=fiducial), client_id=self.websocket_client.uuid
            ),
        )
        led = getattr(self, f"{fiducial}_set_light")
        led.setState(True)


    def clear_fiducials(self):
        if not self.websocket_client:
            return
        send_message_to_server(
            self.websocket_client, 
            create_execute_action_request(
                ClearFiducials(), client_id=self.websocket_client.uuid))
        for led in (self.F0_set_light, self.F1_set_light, self.F2_set_light):
            led.setState(False)