from typing import List, Dict, Any, Tuple
from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QListView,
    QLabel,
    QGridLayout,
    QApplication,
)
from model.chip import Chip
from gui.utils import update_button_style


class ChipGridWidget(QWidget):
    # Chip Grid
    last_selected_signal = Signal(tuple)

    def __init__(self, chip: Chip, parent=None, button_size=40):
        super().__init__(parent=parent)
        self.chip_grid = QGridLayout()
        self.button_size = button_size
        self.chip = chip
        self.last_selected = (0, 0)
        for i in range(self.chip.rows):
            for j in range(self.chip.columns):
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
        self.setLayout(self.chip_grid)

    def select_block(self, x: int, y: int, modifiers):
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
        self.last_selected_signal.emit(self.last_selected)
        # self.update_widget()

    def update_widget(self):
        # update chip grid
        for i in range(self.chip.rows):
            for j in range(self.chip.columns):
                btn = self.chip_grid.itemAtPosition(i, j).widget()
                block = self.chip.blocks[i][j]
                btn = update_button_style(
                    btn,
                    self.button_size,
                    block.selected,
                    block.queued,
                    block.exposed,
                )


class BlockGridWidget(QWidget):
    def __init__(self, chip: Chip, parent=None, button_size=40):
        super().__init__(parent=parent)
        # Block Grid
        self.chip = chip
        self.block_grid = QGridLayout()
        self.block_buttons = {}
        self.last_selected = (0, 0)
        self.last_selected_row = 0
        self.button_size = button_size
        rows = self.chip.blocks[0][0].num_rows
        cols = self.chip.blocks[0][0].num_cols
        for i in range(rows + 1):  # Additional row for labels
            for j in range(cols + 1):  # Additional column for labels
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

        self.setLayout(self.block_grid)

    def set_last_selected(self, last_selected: Tuple[int, int]):
        self.last_selected = last_selected

    def select_row(self, x, modifiers):
        # Deselect all blocks except for the parent block of the selected rows
        for i in range(self.chip.rows):
            for j in range(self.chip.columns):
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
        self.update_widget()

    def update_widget(self):
        # update block grid
        rows = self.chip.blocks[0][0].num_rows
        cols = self.chip.blocks[0][0].num_cols
        for i in range(rows + 1):
            for j in range(cols + 1):
                if (i, j) in self.block_buttons:
                    btn = self.block_buttons[(i, j)]
                    row = self.chip.blocks[self.last_selected[0]][
                        self.last_selected[1]
                    ].rows[i - 1]
                    self.block_buttons[(i, j)] = update_button_style(
                        btn,
                        self.button_size,
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
                    self.block_buttons[(i, j)] = update_button_style(
                        label_button,
                        self.button_size,
                        row.selected,
                        row.queued,
                        row.exposed,
                    )
