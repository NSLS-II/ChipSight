import re
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
from qtpy.QtCore import Qt
from gui.chip_widgets import Chip
from gui.dialogs import LoadChipDialog
from gui.collection_queue import CollectionQueueWidget


class MainWindow(QMainWindow):
    def __init__(self, chip: Chip, config: Dict[str, Any], parent=None):
        super(MainWindow, self).__init__(parent)

        self.chip = chip
        self.config = config
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

        # Chip Grid
        self.chip_grid = QGridLayout()
        button_size = self.config["chip_grid"]["button_size"]
        print(button_size)
        for i in range(8):
            for j in range(8):
                block_address = f"{chr(65+i)}{j+1}"
                btn = QPushButton(block_address)
                btn.setFixedSize(button_size, button_size)
                btn.setFlat(True)  # Add this line to make the button appear flat
                btn.clicked.connect(
                    lambda _, x=i, y=j: self.select_block(
                        x, y, QApplication.keyboardModifiers()
                    )
                )
                self.chip_grid.addWidget(btn, i, j)
        left_layout.addLayout(self.chip_grid)

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

        # Block Grid
        self.block_grid = QGridLayout()
        self.block_buttons = {}
        button_size = self.config["block_grid"]["button_size"]
        for i in range(21):  # Additional row for labels
            for j in range(21):  # Additional column for labels
                if i == 0 and j > 0:  # Top labels
                    label = QLabel(str(j))
                    label.setStyleSheet("font-size: 14px")  # Set font size
                    self.block_grid.addWidget(label, i, j)
                elif j == 0 and i > 0:  # Side labels
                    label_button = QPushButton(chr(96 + i))
                    label_button.setFixedSize(button_size, button_size)
                    label_button.setFlat(
                        True
                    )  # Add this line to make the button appear flat
                    label_button.clicked.connect(
                        lambda _, x=i - 1: self.select_row(
                            x, QApplication.keyboardModifiers()
                        )
                    )
                    self.block_grid.addWidget(label_button, i, j)
                elif i > 0 and j > 0:  # Block buttons
                    btn = QPushButton()  # No address on button
                    btn.setFixedSize(button_size, button_size)
                    btn.setFlat(True)  # Add this line to make the button appear flat
                    self.block_buttons[(i, j)] = btn
                    self.block_grid.addWidget(btn, i, j)
        right_layout.addLayout(self.block_grid)

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
        )
        left_layout.addWidget(self.collection_queue)

        # Push the layouts up by adding stretch at the end
        left_layout.addStretch()
        right_layout.addStretch()

        # Setting the main layout
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.update()

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

    def select_block(self, x, y, modifiers):
        # Start by deselecting all rows of all blocks
        for block_row in self.chip.blocks:
            for block in block_row:
                for row in block.rows:
                    row.selected = False

        if modifiers == Qt.KeyboardModifier.ControlModifier:
            self.chip.blocks[x][y].selected = not self.chip.blocks[x][y].selected
        elif modifiers == Qt.KeyboardModifier.ShiftModifier:
            x1, y1 = self.last_selected
            x2, y2 = x, y
            for i in range(min(x1, x2), max(x1, x2) + 1):
                for j in range(min(y1, y2), max(y1, y2) + 1):
                    self.chip.blocks[i][j].selected = True
        else:
            for block_row in self.chip.blocks:
                for block in block_row:
                    block.selected = False
            self.chip.blocks[x][y].selected = True

        self.last_selected = (x, y)
        self.update()

    def select_row(self, x, modifiers):
        # Deselect all blocks except for the parent block of the selected rows
        for i in range(8):
            for j in range(8):
                if not (i, j) == self.last_selected:
                    self.chip.blocks[i][j].selected = False

        if modifiers == Qt.KeyboardModifier.ControlModifier:
            self.chip.blocks[self.last_selected[0]][self.last_selected[1]].rows[
                x
            ].selected = (
                not self.chip.blocks[self.last_selected[0]][self.last_selected[1]]
                .rows[x]
                .selected
            )
        elif modifiers == Qt.KeyboardModifier.ShiftModifier:
            x1, x2 = self.last_selected_row, x
            for i in range(min(x1, x2), max(x1, x2) + 1):
                self.chip.blocks[self.last_selected[0]][self.last_selected[1]].rows[
                    i
                ].selected = True
        else:
            for row in self.chip.blocks[self.last_selected[0]][
                self.last_selected[1]
            ].rows:
                row.selected = False
            self.chip.blocks[self.last_selected[0]][self.last_selected[1]].rows[
                x
            ].selected = True
        self.last_selected_row = x
        self.update()

    def update_button_style(
        self, button, size, selected=False, queued="not queued", exposed="not exposed"
    ):
        # Define base style
        style = f"font-size: 14px; min-width: {size}px; min-height: {size}px;"
        base_color = "#ffffff"  # Base color for unselected state
        border_color = "#ffffff"  # Base border color for unselected state

        # Define colors for different states
        # https://rgbcolorcode.com
        state_colors = {
            "partially queued": "#ff8066",  # Salmon
            "queued": "#e62600",  # Ferrari red
            "partially exposed": "#fff7cc",  # Lemon chiffon
            "exposed": "#ffee99",  # Flavescent
        }

        # Based on queued state, update border color
        if queued in state_colors:
            border_color = state_colors[queued]

        # Based on exposed state, update base color
        if exposed in state_colors:
            base_color = state_colors[exposed]

        # If selected, darken the color by subtracting from RGB values
        if selected:
            base_color = "#" + "".join(
                [
                    hex(max(0, int(base_color[i : i + 2], 16) - int("20", 16)))[
                        2:
                    ].zfill(2)
                    for i in range(1, 6, 2)
                ]
            )
            border_color = "#" + "".join(
                [
                    hex(max(0, int(border_color[i : i + 2], 16) - int("20", 16)))[
                        2:
                    ].zfill(2)
                    for i in range(1, 6, 2)
                ]
            )

        style += f"background-color: {base_color}; border: 3px solid {border_color};"
        button.setStyleSheet(style)

    def update(self):
        # update chip label
        self.chip_label.setText(f"Current chip: {self.chip.name}")

        # update chip grid
        for i in range(8):
            for j in range(8):
                btn = self.chip_grid.itemAtPosition(i, j).widget()
                block = self.chip.blocks[i][j]
                self.update_button_style(
                    btn,
                    self.config["chip_grid"]["button_size"],
                    block.selected,
                    block.queued,
                    block.exposed,
                )

        # update block label
        block_address = f"{chr(65+self.last_selected[0])}{self.last_selected[1]+1}"
        self.block_label.setText(f"Current city block: {block_address}")

        # update block grid
        for i in range(21):
            for j in range(21):
                if (i, j) in self.block_buttons:
                    btn = self.block_buttons[(i, j)]
                    row = self.chip.blocks[self.last_selected[0]][
                        self.last_selected[1]
                    ].rows[i - 1]
                    self.update_button_style(
                        btn,
                        self.config["block_grid"]["button_size"],
                        row.selected,
                        row.queued,
                        row.exposed,
                    )
                elif i == 0 and j > 0:
                    label = self.block_grid.itemAtPosition(i, j).widget()
                    label.setStyleSheet("font-size: 14px")
                elif j == 0 and i > 0:
                    label_button = self.block_grid.itemAtPosition(i, j).widget()
                    row = self.chip.blocks[self.last_selected[0]][
                        self.last_selected[1]
                    ].rows[i - 1]
                    self.update_button_style(
                        label_button,
                        self.config["block_grid"]["button_size"],
                        row.selected,
                        row.queued,
                        row.exposed,
                    )
