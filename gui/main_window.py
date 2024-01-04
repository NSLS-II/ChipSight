from datetime import datetime
from typing import Any, Dict

from qmicroscope.microscope import Microscope
from qmicroscope.plugins.c2c_plugin import C2CPlugin
from qmicroscope.plugins.crosshair_plugin import CrossHairPlugin
from qmicroscope.plugins.mousewheel_camera_zoom import MouseWheelCameraZoomPlugin
from qtpy import QtCore
from qtpy.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QAction
)

from gui.chip_widgets import BlockGridWidget, ChipGridWidget
from gui.collection_queue import CollectionQueueWidget
from gui.dialogs import LoginDialog, GovernorStateMachineDialog
from gui.utils import create_execute_action_request, send_message_to_server
from gui.websocket_client import WebSocketClient
from gui.widgets import ControlPanelWidget
from model.chip import Chip
from model.comm_protocol import (
    ClearQueue,
    ClickToCenter,
    CollectNeighborhood,
    CollectRow,
    ErrorResponse,
    ExecuteActionResponse,
    Message,
    PayloadType,
    PointDelta,
    QueueActionResponse,
    RemoveFromQueue,
    StatusResponse,
    VideoDimensions,
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
        self.websocket_client.connection_status.connect(self.handle_connection_status)
        self.websocket_client.start()

        self.setWindowTitle("ChipSight")
        self.tool_bar = self.addToolBar("General")
        self.governor_state_dialog_open_action = QAction("&Governor State", self)
        self.tool_bar.addAction(self.governor_state_dialog_open_action)
        self.governor_state_dialog_open_action.triggered.connect(self.open_governor_dialog)

        self.create_chip_grid_widget()
        self.create_qmicroscope_widget()
        self.create_control_panel_widget()
        self.create_block_grid_widget()

        # Setting the main layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        if not self.config.get("test", False):
            self.show_login_modal()

        self.update()

    def open_governor_dialog(self):
        self.governor_dialog = GovernorStateMachineDialog(self.websocket_client)
        self.governor_dialog.show()


    def create_chip_grid_widget(self):
        self.chip_grid = ChipGridWidget(
            chip=self.chip, button_size=self.config["chip_grid"]["button_size"]
        )
        self.chip_grid.last_selected_signal.connect(self.set_last_selected)

        # Chip grid dock
        self.chip_grid_dock = QDockWidget("Current Chip: Chip01", self)
        self.chip_grid_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self.chip_grid_dock.setAllowedAreas(
            QtCore.Qt.DockWidgetArea.LeftDockWidgetArea
            | QtCore.Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.addDockWidget(
            QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.chip_grid_dock
        )
        self.chip_grid_dock.setWidget(self.chip_grid)

    def create_block_grid_widget(self):
        # Block Label
        self.block_grid = BlockGridWidget(
            self.chip, button_size=self.config["block_grid"]["button_size"]
        )
        self.block_grid_dock = QDockWidget("Current city block: A1", self)
        self.block_grid_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self.block_grid_dock.setAllowedAreas(
            QtCore.Qt.DockWidgetArea.LeftDockWidgetArea
            | QtCore.Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.addDockWidget(
            QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.block_grid_dock
        )
        self.block_grid_dock.setWidget(self.block_grid)

    def create_qmicroscope_widget(self):
        # Setup Q microscope
        plugins = [C2CPlugin, CrossHairPlugin, MouseWheelCameraZoomPlugin]
        self.microscope = Microscope(self, viewport=False, plugins=plugins)  # type: ignore
        self.microscope.scale = [0, 400]
        self.microscope.fps = 30
        # Adding camera urls to MouseWheelCameraZoomPlugin
        self.microscope.plugins["MouseWheelCameraZoomPlugin"].urls = self.config[
            "sample_cam"
        ]["urls"]
        # C2CPlugin provides pixel co-ordinates of click, and zoom level
        self.microscope.plugins["C2CPlugin"].clicked_signal.clicked.connect(
            self.click_to_center
        )
        self.microscope.acquire(True)
        self.microscope_dock = QDockWidget("Microscope", self)
        self.microscope_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self.microscope_dock.setAllowedAreas(
            QtCore.Qt.DockWidgetArea.LeftDockWidgetArea
            | QtCore.Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.addDockWidget(
            QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.microscope_dock
        )
        self.microscope_dock.setWidget(self.microscope)

    def create_control_panel_widget(self):
        # Left Layout (Queue List, Action Buttons, and Status Window)
        left_layout = QVBoxLayout()

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

        self.control_panel_dock = QDockWidget("Control Panel", self)
        self.control_panel_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self.control_panel_dock.setAllowedAreas(
            QtCore.Qt.DockWidgetArea.LeftDockWidgetArea
            | QtCore.Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.addDockWidget(
            QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.control_panel_dock
        )
        self.control_panel_widget = QWidget()
        self.control_panel_widget.setLayout(left_layout)
        self.control_panel_dock.setWidget(self.control_panel_widget)

        # Status window
        self.status_window = QTextEdit()
        self.status_window.setReadOnly(True)
        self.status_label = QLabel("Status:")
        left_layout.addWidget(self.status_label)
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
        self.collection_queue_widget.setMaximumHeight(200)
        left_layout.addWidget(self.collection_queue_widget)

        self.connection_status_label = QLabel("Connection Status: ")
        self.connection_status_value_label = QLabel("Establishing connection...")
        self.reconnect_button = QPushButton("Reconnect")
        self.reconnect_button.setEnabled(False)
        self.reconnect_button.clicked.connect(self.reconnect)
        connection_label_layouts = QHBoxLayout()
        connection_label_layouts.addWidget(self.connection_status_label)
        connection_label_layouts.addWidget(self.connection_status_value_label)
        connection_label_layouts.addWidget(self.reconnect_button)
        left_layout.addLayout(connection_label_layouts)

        # Push the layouts up by adding stretch at the end
        left_layout.addStretch()

    def click_to_center(self, data):
        y_delta = data["y_pixel_delta"]
        x_delta = data["x_pixel_delta"]
        pd = PointDelta(x_delta=x_delta, y_delta=y_delta)
        vd = VideoDimensions(
            width=self.microscope.view.viewport().width(),
            height=self.microscope.view.viewport().height(),
        )
        zoom_level = self.microscope.plugins[
            "MouseWheelCameraZoomPlugin"
        ].current_url_index
        c2c_payload = ClickToCenter(
            pixel_delta=pd, video_dimensions=vd, zoom_level=zoom_level
        )
        print(c2c_payload)
        send_message_to_server(
            self.websocket_client,
            create_execute_action_request(c2c_payload, self.websocket_client.uuid),
        )

    def handle_connection_status(self, connection_status: str):
        self.connection_status_value_label.setText(connection_status)
        if connection_status == "Disconnected":
            self.reconnect_button.setEnabled(True)
        else:
            self.reconnect_button.setEnabled(False)

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
        if isinstance(message, Message):
            if isinstance(message.metadata, QueueActionResponse):
                self.handle_queue_action(message.metadata, message.payload)
            elif isinstance(message.metadata, ExecuteActionResponse):
                self.status_window.append(
                    f"{message.metadata.timestamp.strftime('%H:%M:%S')} : {message.metadata.status_msg}"
                )
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
        else:
            self.status_window.append(
                f"{datetime.now()} : Unhandled response - {message}"
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
        self.chip_grid_dock.setWindowTitle(f"Current chip: {self.chip.name}")

        self.chip_grid.update_widget()

        # update block label
        block_address = f"{chr(65+self.chip_grid.last_selected[0])}{self.chip_grid.last_selected[1]+1}"
        self.block_grid_dock.setWindowTitle(f"Current city block: {block_address}")

        self.block_grid.update_widget()

    def reconnect(self):
        self.websocket_client.start()
