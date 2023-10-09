from typing import Any, Dict

from qtpy import QtCore
from qtpy.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from gui.chip_widgets import BlockGridWidget, ChipGridWidget
from gui.collection_queue import CollectionQueueWidget
from gui.dialogs import LoginDialog
from gui.microscope.microscope import Microscope
from gui.microscope.plugins.c2c_plugin import C2CPlugin
from gui.microscope.plugins.crosshair_plugin import CrossHairPlugin
from gui.websocket_client import WebSocketClient
from gui.widgets import ControlPanelWidget
from model.chip import Chip
from model.comm_protocol import (
    ClearQueue,
    CollectNeighborhood,
    CollectRow,
    ErrorResponse,
    Message,
    PayloadType,
    QueueActionResponse,
    RemoveFromQueue,
    StatusResponse,
)


class MainWindow(QMainWindow):
    def __init__(self, chip: Chip, config: Dict[str, Any], parent=None):
        super(MainWindow, self).__init__(parent)

        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.chip = chip
        self.config = config
        self.server_url = f'{config["server"]["url"]}:{config["server"]["port"]}'

        self.websocket_client = WebSocketClient(server_url=self.server_url)
        self.websocket_client.message_received.connect(self.handle_server_response)
        self.websocket_client.start()

        self.setWindowTitle("ChipSight")

        # Main layout
        main_layout = QHBoxLayout()

        # Left Layout (Chip Grid, Queue List, Action Buttons, and Status Window)
        left_layout = QVBoxLayout()
        main_layout.addLayout(left_layout)

        # Chip Label
        self.chip_label = QLabel("Current chip: Chip01")
        left_layout.addWidget(self.chip_label)

        self.chip_grid = ChipGridWidget(
            chip=self.chip, button_size=self.config["chip_grid"]["button_size"]
        )
        self.chip_grid.last_selected_signal.connect(self.set_last_selected)
        left_layout.addWidget(self.chip_grid)

        # Data collection parameters
        left_layout.addWidget(QLabel("Data collection parameters"))

        self.collection_parameters = {
            "exposure_time": {
                "label": "Exposure time [ms]",
                "default_value": "20",
                "widget": None,
            }
            # Add more parameters here in the future...
        }

        for param_name, param_info in self.collection_parameters.items():
            param_layout = QHBoxLayout()
            param_label = QLabel(param_info["label"])
            param_field = QLineEdit()
            param_field.setText(param_info["default_value"])
            param_layout.addWidget(param_label)
            param_layout.addWidget(param_field)
            left_layout.addLayout(param_layout)
            param_info["widget"] = param_field

        # F0 to F2 buttons
        fidu_buttons = ControlPanelWidget(websocket_client=self.websocket_client)
        left_layout.addWidget(fidu_buttons)

        # left_layout.addWidget(nudge_widget)

        # Right Layout (Block Label and Block Grid)
        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout)

        # Setup Q microscope
        self.microscope = Microscope(self, viewport=False, plugins=[C2CPlugin, CrossHairPlugin])  # type: ignore
        self.microscope.scale = [0, 400]
        self.microscope.fps = 30
        self.microscope.url = self.config["sample_cam"]["url"]
        right_layout.addWidget(self.microscope)
        self.microscope.acquire(True)

        # Block Label
        self.block_label = QLabel("Current city block: A1")
        right_layout.addWidget(self.block_label)

        self.block_grid = BlockGridWidget(
            self.chip, button_size=self.config["block_grid"]["button_size"]
        )
        right_layout.addWidget(self.block_grid)

        # Status window
        self.status_window = QTextEdit()
        self.status_window.setReadOnly(True)
        left_layout.addWidget(self.status_window)

        self.last_selected = (0, 0)
        self.last_selected_row = 0

        self.collection_queue_widget = CollectionQueueWidget(
            self.chip,
            self.last_selected,
            self.collection_parameters,
            self.status_window,
            self.websocket_client,
        )
        left_layout.addWidget(self.collection_queue_widget)

        # Push the layouts up by adding stretch at the end
        left_layout.addStretch()
        right_layout.addStretch()

        # Setting the main layout
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        if not self.config.get("test", False):
            self.show_login_modal()

        self.update()

    def show_login_modal(self):
        self.login_modal = LoginDialog(
            server_url=f"http://{self.server_url}/gui/login/{self.websocket_client.uuid}",
            uuid=self.websocket_client.uuid,
        )

    def clean_up(self):
        self.microscope.acquire(False)

    def closeEvent(self, event) -> None:
        self.clean_up()
        event.accept()

    def set_last_selected(self, value: "tuple[int, int]"):
        self.last_selected = value
        self.block_grid.set_last_selected(value)
        self.collection_queue_widget.set_last_selected(value)
        self.update()

    def handle_server_response(self, message: Message):
        if isinstance(message.metadata, QueueActionResponse):
            self.handle_queue_action(message.metadata, message.payload)
        elif isinstance(message.metadata, ErrorResponse):
            self.status_window.setTextColor(QtCore.Qt.GlobalColor.red)
            self.status_window.append(
                f"{message.metadata.timestamp.strftime('%H:%M:%S')} : {message.metadata.status_msg}"
            )
            self.status_window.setTextColor(QtCore.Qt.GlobalColor.black)
        elif isinstance(message.metadata, StatusResponse):
            self.status_window.append(
                f"{message.metadata.timestamp.strftime('%H:%M:%S')} : {message.metadata.status_msg}"
            )
        else:
            self.status_window.append(
                f"{message.metadata.timestamp.strftime('%H:%M:%S')} : Unhandled response - {message.metadata.__class__.__name__}"
            )

    def handle_queue_action(
        self, metadata: QueueActionResponse, payload: PayloadType | None
    ):
        if metadata.status_msg:
            self.status_window.append(
                f"{metadata.timestamp.strftime('%H:%M:%S')} : {metadata.status_msg}"
            )
        if isinstance(payload, (CollectNeighborhood, CollectRow)):
            self.collection_queue_widget.collection_queue.add_to_queue(payload)
        elif isinstance(payload, ClearQueue):
            self.collection_queue_widget.collection_queue.clear_queue()
        elif isinstance(payload, RemoveFromQueue):
            self.collection_queue_widget.collection_queue.removeRow(payload.index)
        else:
            self.status_window.append(
                f"{metadata.timestamp.strftime('%H:%M:%S')} : Unhandled queue action - {payload.__class__.__name__}"
            )

    def update(self):
        # update chip label
        self.chip_label.setText(f"Current chip: {self.chip.name}")

        self.chip_grid.update_widget()

        # update block label
        block_address = f"{chr(65+self.chip_grid.last_selected[0])}{self.chip_grid.last_selected[1]+1}"
        self.block_label.setText(f"Current city block: {block_address}")

        self.block_grid.update_widget()
