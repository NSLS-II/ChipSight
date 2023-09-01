import re
import json
from typing import Dict, Any
from qtpy.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QTextEdit,
)
from datetime import datetime
from qtpy.QtCore import Qt
from model.chip import Chip
from gui.dialogs import LoadChipDialog
from gui.collection_queue import CollectionQueueWidget
from gui.chip_widgets import ChipGridWidget, BlockGridWidget
from gui.websocket_client import WebSocketClient
from model.comm_protocol import Protocol


class MainWindow(QMainWindow):
    def __init__(self, chip: Chip, config: Dict[str, Any], parent=None):
        super(MainWindow, self).__init__(parent)

        self.chip = chip
        self.config = config

        self.websocket_client = WebSocketClient(
            server_url=config["server"]["url"], server_port=config["server"]["port"]
        )
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

        # Right Layout (Block Label and Block Grid)
        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout)

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
        right_layout.addWidget(self.status_window)

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

        self.update()

    def set_last_selected(self, value: "tuple[int, int]"):
        self.last_selected = value
        self.block_grid.set_last_selected(value)
        self.collection_queue.set_last_selected(value)
        self.update()

    def handle_server_message(self, message: str):
        data = json.loads(message)
        if self.p.Labels.BROADCAST in data:
            bcast_data = data[self.p.Labels.BROADCAST]
            if self.p.Labels.ACTION in bcast_data:
                action = bcast_data[self.p.Labels.ACTION]
                metadata = bcast_data[self.p.Labels.METADATA]
                if action == self.p.Actions.ADD_TO_QUEUE:
                    req = metadata[self.p.Labels.REQUEST]
                    self.collection_queue.collection_queue.add_to_queue(
                        req[self.p.Labels.ADDRESS]
                    )
                if action == self.p.Actions.CLEAR_QUEUE:
                    self.collection_queue.collection_queue.queue = []

            if self.p.Labels.STATUS_MSG in bcast_data:
                self.status_window.append(
                    f"{datetime.now().strftime('%H:%M:%S')} : {bcast_data[self.p.Labels.STATUS_MSG]}"
                )
        print(data)

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
