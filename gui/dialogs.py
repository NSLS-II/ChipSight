from qtpy.QtCore import QUrl
from qtpy.QtGui import QDesktopServices
from qtpy.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)
from gui.utils import send_message_to_server, create_execute_action_request
from model.comm_protocol import SetGovernorState
from .websocket_client import WebSocketClient

class LoadChipDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)


class LoginDialog(QDialog):
    def __init__(self, parent=None, server_url=None, uuid=None):
        super().__init__(parent=parent)
        layout = QVBoxLayout()

        self.message = QLabel("Please login to continue.")
        layout.addWidget(self.message)

        self.button_panel_layout = QHBoxLayout()
        self.reconnect_server_button = QPushButton("Reconnect Server")
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(
            self.open_browser
        )  # Connect the button to the slot

        self.button_panel_layout.addWidget(self.reconnect_server_button)
        self.button_panel_layout.addWidget(self.login_button)

        layout.addLayout(self.button_panel_layout)

        self.setLayout(layout)
        self.resize(300, 150)
        self.setModal(True)
        self.show()

        self.server_url = server_url
        self.programmatic_close = False

    def closeEvent(self, event):
        if not self.programmatic_close:
            QApplication.quit()
        else:
            event.accept()

    def open_browser(self):
        if self.server_url:
            QDesktopServices.openUrl(QUrl(self.server_url))

class GovernorStateMachineDialog(QDialog):
    def __init__(self, websocket_client: WebSocketClient):
        super().__init__()
        self.setWindowTitle("Set Governor State")
        self.CE = QPushButton("CE", self)
        self.CA = QPushButton("CA", self)
        self.CD = QPushButton("CD", self)
        self.CA.clicked.connect(self.go_to_ca)
        self.CD.clicked.connect(self.go_to_cd)
        self.CE.clicked.connect(self.go_to_ce)

        # self.arrowWidget = ArrowWidget(self)
        # self.arrowWidget.connectButtons(self.button1, self.button2)

        layout = QHBoxLayout()
        layout.addWidget(self.CE)
        layout.addWidget(self.CA)
        # layout.addWidget(self.arrowWidget)  # This widget draws arrows between the buttons
        layout.addWidget(self.CD)

        self.setLayout(layout)
        self.websocket_client = websocket_client
    
    def go_to_ce(self):
        send_message_to_server(self.websocket_client, 
                               create_execute_action_request(SetGovernorState(state="CE"), 
                                                             client_id=self.websocket_client.uuid))

    def go_to_ca(self):
        send_message_to_server(self.websocket_client, 
                               create_execute_action_request(SetGovernorState(state="CA"), 
                                                             client_id=self.websocket_client.uuid))
    
    def go_to_cd(self):
        send_message_to_server(self.websocket_client, 
                               create_execute_action_request(SetGovernorState(state="CD"), 
                                                             client_id=self.websocket_client.uuid))