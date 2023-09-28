from qtpy.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QHBoxLayout,
    QApplication,
)
from qtpy.QtGui import QDesktopServices
from qtpy.QtCore import QUrl, Qt


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
