import re
import json
from typing import Dict, Any
from qtpy.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QTextEdit,
    QToolButton
)
from datetime import datetime
from qtpy import QtCore
from model.chip import Chip
from gui.dialogs import LoadChipDialog, LoginDialog
from gui.collection_queue import CollectionQueueWidget
from gui.chip_widgets import ChipGridWidget, BlockGridWidget
from gui.websocket_client import WebSocketClient
from model.comm_protocol import Protocol

from gui.microscope.microscope import Microscope
from gui.microscope.plugins.c2c_plugin import C2CPlugin
from gui.microscope.plugins.crosshair_plugin import CrossHairPlugin

from gui.utils import send_message_to_server


class MainWindow(QMainWindow):
    def __init__(self, chip: Chip, config: Dict[str, Any], parent=None):
        super(MainWindow, self).__init__(parent)

        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.chip = chip
        self.config = config
        self.server_url = f'{config["server"]["url"]}:{config["server"]["port"]}'

        self.websocket_client = WebSocketClient(server_url=self.server_url)
        self.websocket_client.message_received.connect(self.handle_server_message)
        self.websocket_client.start()

        self.setWindowTitle("ChipSight")

        # Main layout
        main_layout = QHBoxLayout()

        # Left Layout (Chip Grid, Queue List, Action Buttons, and Status Window)
        left_layout = QVBoxLayout()
        main_layout.addLayout(left_layout)

        self.load_chip_button = QPushButton("Load chip")
        self.load_chip_button.clicked.connect(self.load_chip)
        left_layout.addWidget(self.load_chip_button)

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
        fidu_buttons = QGridLayout()

        F0_button = QPushButton('F0')
        F0_button.clicked.connect(self.go_to_F0)
        set_F0_button = QPushButton('Set F0')
        set_F0_button.clicked.connect(self.set_F0)


        F1_button = QPushButton('F1')
        F1_button.clicked.connect(self.go_to_F1)
        set_F1_button = QPushButton('Set F1')
        set_F1_button.clicked.connect(self.set_F1)

        F2_button = QPushButton('F2')
        F2_button.clicked.connect(self.go_to_F2)
        set_F2_button = QPushButton('Set F2')
        set_F2_button.clicked.connect(self.set_F2)


        fidu_buttons.addWidget(F0_button, 0, 0)
        fidu_buttons.addWidget(set_F0_button, 0, 1)
        fidu_buttons.addWidget(F1_button, 1, 0)
        fidu_buttons.addWidget(set_F1_button, 1, 1)
        fidu_buttons.addWidget(F2_button, 2, 0)
        fidu_buttons.addWidget(set_F2_button, 2, 1)
        left_layout.addLayout(fidu_buttons)

        nudge_buttons = QHBoxLayout()
        self.nudge_amount = QLineEdit("10")

        up_button = QToolButton()
        up_button.setArrowType(QtCore.Qt.UpArrow)
        up_button.clicked.connect(self.nudge_up)
        down_button = QToolButton()
        down_button.setArrowType(QtCore.Qt.DownArrow)
        down_button.clicked.connect(self.nudge_down)

        left_button = QToolButton()
        left_button.setArrowType(QtCore.Qt.LeftArrow)
        left_button.clicked.connect(self.nudge_left)

        right_button = QToolButton()
        right_button.setArrowType(QtCore.Qt.RightArrow)
        right_button.clicked.connect(self.nudge_right)

        nudge_buttons.addWidget(self.nudge_amount)
        nudge_buttons.addWidget(up_button)
        nudge_buttons.addWidget(down_button)
        nudge_buttons.addWidget(left_button)
        nudge_buttons.addWidget(right_button)
        left_layout.addLayout(nudge_buttons)

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

        self.collection_queue = CollectionQueueWidget(
            self.chip,
            self.last_selected,
            self.collection_parameters,
            self.status_window,
            self.websocket_client,
        )
        left_layout.addWidget(self.collection_queue)

        # Push the layouts up by adding stretch at the end
        left_layout.addStretch()
        right_layout.addStretch()

        # Setting the main layout
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Setup protocol
        self.p = Protocol()

        self.show_login_modal()

        self.update()

    def go_to_F0(self):
        send_message_to_server(self.websocket_client, {self.p.Key.ACTION: self.p.Action.MOVE_GONIO, 
                                                       self.p.Key.METADATA: {"x":-25400/2, "y":-25400/2}})

    def go_to_F1(self):
        send_message_to_server(self.websocket_client, {self.p.Key.ACTION: self.p.Action.MOVE_GONIO, 
                                                       self.p.Key.METADATA: {"x":25400/2, "y":-25400/2}})
    
    def go_to_F2(self):
        send_message_to_server(self.websocket_client, {self.p.Key.ACTION: self.p.Action.MOVE_GONIO, 
                                                       self.p.Key.METADATA: {"x":-25400/2, "y":25400/2}})

    def nudge_up(self):
        send_message_to_server(self.websocket_client, {self.p.Key.ACTION: self.p.Action.NUDGE_GONIO, 
                                                       self.p.Key.METADATA: {"x":0, "y":int(self.nudge_amount.text())}})
    
    def nudge_down(self):
        send_message_to_server(self.websocket_client, {self.p.Key.ACTION: self.p.Action.NUDGE_GONIO, 
                                                       self.p.Key.METADATA: {"x":0, "y":-int(self.nudge_amount.text())}})
    
    def nudge_left(self):
        send_message_to_server(self.websocket_client, {self.p.Key.ACTION: self.p.Action.NUDGE_GONIO, 
                                                       self.p.Key.METADATA: {"x":-int(self.nudge_amount.text()), "y":0}})
    
    def nudge_right(self):
        send_message_to_server(self.websocket_client, {self.p.Key.ACTION: self.p.Action.NUDGE_GONIO, 
                                                       self.p.Key.METADATA: {"x":int(self.nudge_amount.text()), "y":0}})

    def set_F0(self):
        send_message_to_server(self.websocket_client, {self.p.Key.ACTION: self.p.Action.SET_FIDUCIAL,
                                                       self.p.Key.METADATA: {"fiducial_name": "F0"}})
    
    def set_F1(self):
        send_message_to_server(self.websocket_client, {self.p.Key.ACTION: self.p.Action.SET_FIDUCIAL,
                                                       self.p.Key.METADATA: {"fiducial_name": "F1"}})
        
    def set_F2(self):
        send_message_to_server(self.websocket_client, {self.p.Key.ACTION: self.p.Action.SET_FIDUCIAL,
                                                       self.p.Key.METADATA: {"fiducial_name": "F2"}})

    def show_login_modal(self):
        self.login_modal = LoginDialog(
            server_url=f"http://{self.server_url}/gui_login/{self.websocket_client.uuid}",
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
        self.collection_queue.set_last_selected(value)
        self.update()

    def handle_server_message(self, message: str):
        data = json.loads(message)
        print(f"Server Message: {data}")
        # Check if data is a broadcast
        if self.p.Key.BROADCAST in data:
            bcast_data = data[self.p.Key.BROADCAST]
            # Check if broadcast contains an action
            if self.p.Key.ACTION in bcast_data:
                # Get the action and related metadata
                action = bcast_data[self.p.Key.ACTION]
                metadata = bcast_data[self.p.Key.METADATA]
                # Add to queue
                if action == self.p.Action.ADD_TO_QUEUE:
                    req = metadata[self.p.Key.REQUEST]
                    self.collection_queue.collection_queue.add_to_queue(
                        req[self.p.Key.ADDRESS]
                    )
                # Clear queue
                if action == self.p.Action.CLEAR_QUEUE:
                    self.collection_queue.collection_queue.queue = []
            # Check if broadcast contains a status message
            if self.p.Key.STATUS_MSG in bcast_data:
                self.status_window.append(
                    f"{datetime.now().strftime('%H:%M:%S')} : {bcast_data[self.p.Key.STATUS_MSG]}"
                )
        # Otherwise its unicast data
        elif self.p.Key.UNICAST in data:
            unicast_data = data[self.p.Key.UNICAST]
            if self.p.Key.LOGIN in unicast_data:
                if unicast_data[self.p.Key.LOGIN] == self.p.Status.SUCCESS:
                    self.login_modal.programmatic_close = True
                    self.login_modal.close()

            # Check if broadcast contains a status message
            if self.p.Key.STATUS_MSG in unicast_data:
                self.status_window.append(
                    f"{datetime.now().strftime('%H:%M:%S')} : {unicast_data[self.p.Key.STATUS_MSG]}"
                )

    def load_chip(self):
        dialog = LoadChipDialog(self)
        dialog.name_edit.setText(self.chip.name)
        if dialog.exec():
            new_name = dialog.name_edit.text().strip()
            if self.valid_filename(new_name):
                self.chip.change_name(new_name)
                self.chip_label.setText(f"Current chip: {self.chip.name}")
                for block_row in self.chip.blocks:
                    for block in block_row:
                        block.selected = False
                        block.queued = "not queued"
                        block.exposed = "not exposed"
                        for row in block.rows:
                            row.selected = False
                            row.queued = "not queued"
                            row.exposed = "not exposed"
                self.update()
            else:
                self.status_window.append(
                    "Invalid chip name. Please provide a valid name."
                )

    def valid_filename(self, new_name):
        # Check that new_name is not None and doesn't start with a dot
        if not new_name or new_name.startswith("."):
            return False

        # Check for invalid characters (Linux/UNIX and Windows)
        # Linux/UNIX disallows null bytes and slashes in filenames, Windows disallows a number of special characters
        invalid_chars = re.compile(r'[\x00/\x1F<>:"\\|?*]')

        if invalid_chars.search(new_name):
            return False

        # Check for reserved filenames in Windows
        reserved_names = [
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        ]

        # Using case-insensitive match as Windows is case-insensitive
        if new_name.upper() in reserved_names:
            return False

        return True

    def update(self):
        # update chip label
        self.chip_label.setText(f"Current chip: {self.chip.name}")

        self.chip_grid.update_widget()

        # update block label
        block_address = f"{chr(65+self.chip_grid.last_selected[0])}{self.chip_grid.last_selected[1]+1}"
        self.block_label.setText(f"Current city block: {block_address}")

        self.block_grid.update_widget()
