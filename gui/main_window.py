import re
from qtpy.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QListView,
    QLineEdit,
    QTextEdit,
)
from qtpy.QtCore import Qt
from gui.collection_queue import CollectionQueue
from gui.dialogs import LoadChipDialog


class MainWindow(QMainWindow):
    def __init__(self, chip, parent=None):
        super(MainWindow, self).__init__(parent)

        self.chip = chip
        self.setWindowTitle("chipgui")

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
        for i in range(8):
            for j in range(8):
                block_address = f"{chr(65+i)}{j+1}"
                btn = QPushButton(block_address)
                btn.setFixedSize(60, 60)
                btn.setFlat(True)  # Add this line to make the button appear flat
                btn.clicked.connect(
                    lambda _, x=i, y=j: self.select_block(
                        x, y, QApplication.keyboardModifiers()
                    )
                )
                self.chip_grid.addWidget(btn, i, j)
        left_layout.addLayout(self.chip_grid)

        # Add to queue Button
        self.add_to_queue_button = QPushButton("Add to queue")
        self.add_to_queue_button.clicked.connect(self.add_to_queue)
        left_layout.addWidget(self.add_to_queue_button)

        # Queue list
        self.collection_queue = CollectionQueue()
        self.queue_list = QListView()
        self.queue_list.setModel(self.collection_queue)  # Queue model
        left_layout.addWidget(self.queue_list)

        # Clear queue Button
        self.clear_queue_button = QPushButton("Clear queue")
        self.clear_queue_button.clicked.connect(self.clear_queue)
        left_layout.addWidget(self.clear_queue_button)

        # Collect queue Button
        self.collect_queue_button = QPushButton("Collect queue")
        self.collect_queue_button.clicked.connect(self.collect_queue)
        left_layout.addWidget(self.collect_queue_button)

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
        for i in range(21):  # Additional row for labels
            for j in range(21):  # Additional column for labels
                if i == 0 and j > 0:  # Top labels
                    label = QLabel(str(j))
                    label.setStyleSheet("font-size: 14px")  # Set font size
                    self.block_grid.addWidget(label, i, j)
                elif j == 0 and i > 0:  # Side labels
                    label_button = QPushButton(chr(96 + i))
                    label_button.setFixedSize(30, 30)
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
                    btn.setFixedSize(30, 30)
                    btn.setFlat(True)  # Add this line to make the button appear flat
                    self.block_buttons[(i, j)] = btn
                    self.block_grid.addWidget(btn, i, j)
        right_layout.addLayout(self.block_grid)

        # Status window
        self.status_window = QTextEdit()
        self.status_window.setReadOnly(True)
        right_layout.addWidget(self.status_window)

        # Push the layouts up by adding stretch at the end
        left_layout.addStretch()
        right_layout.addStretch()

        # Setting the main layout
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.last_selected = (0, 0)
        self.last_selected_row = 0
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

    # Add selected blocks and rows to queue
    def add_to_queue(self):
        last_block = self.chip.blocks[self.last_selected[0]][self.last_selected[1]]
        selected_rows = [row for row in last_block.rows if row.selected]
        if selected_rows:  # last selected block contains selected rows
            for row in selected_rows:
                row.queued = "queued"
                self.collection_queue.add_to_queue(row.address)
            last_block.queued = "partially queued"
            if all(
                row.queued == "queued" for row in last_block.rows[:-1]
            ):  # exclude label row
                last_block.queued = "queued"
        else:  # last selected block does not contain selected rows
            for block_row in self.chip.blocks:
                for block in block_row:
                    if block.selected:
                        block.queued = "queued"
                        for row in block.rows:
                            row.queued = "queued"
                        self.collection_queue.add_to_queue(block.address)
        self.update()

    # Clear the queue
    def clear_queue(self):
        for block_row in self.chip.blocks:
            for block in block_row:
                block.queued = "not queued"
                for row in block.rows:
                    row.queued = "not queued"
        self.collection_queue.remove_from_queue()
        self.update()

    def collect_queue(self):
        while self.collection_queue.queue:
            container_address = self.collection_queue.queue.pop(0)
            if len(container_address) == 2:  # it's a block
                self.collect_block(container_address)
            else:  # it's a row
                self.collect_row(container_address)
        self.update()

    def collect_block(self, block_address):
        x = ord(block_address[0]) - 65
        y = int(block_address[1:]) - 1
        block = self.chip.blocks[x][y]
        block.exposed = "exposed"
        block.queued = "not queued"
        for row in block.rows:
            row.exposed = "exposed"
            row.queued = "not queued"
        exposure_time = self.collection_parameters["exposure_time"]["widget"].text()
        exposure_time_label = self.collection_parameters["exposure_time"]["label"]
        self.status_window.append(
            f"Collecting block {block_address} with {exposure_time_label} = {exposure_time}"
        )

    def collect_row(self, row_address):
        x = ord(row_address[0]) - 65
        y = int(row_address[1]) - 1
        row_id = ord(row_address[2]) - 97
        row = self.chip.blocks[x][y].rows[row_id]
        row.exposed = "exposed"
        row.queued = "not queued"
        exposure_time = self.collection_parameters["exposure_time"]["widget"].text()
        exposure_time_label = self.collection_parameters["exposure_time"]["label"]
        self.status_window.append(
            f"Collecting row {row_address} with {exposure_time_label} = {exposure_time}"
        )

        block = self.chip.blocks[x][y]
        if block.exposed == "not exposed":
            block.exposed = "partially exposed"
        if all(
            row.exposed == "exposed" for row in block.rows[:-1]
        ):  # exclude label row
            block.exposed = "exposed"
        if all(
            row.queued == "not queued" for row in block.rows[:-1]
        ):  # exclude label row
            block.queued = "not queued"

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
                    btn, 60, block.selected, block.queued, block.exposed
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
                        btn, 30, row.selected, row.queued, row.exposed
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
                        label_button, 30, row.selected, row.queued, row.exposed
                    )
