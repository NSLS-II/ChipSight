from typing import List, Dict, Any, Tuple
from qtpy.QtCore import Qt, QAbstractListModel, QModelIndex
from qtpy.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListView, QTextEdit
from gui.chip_widgets import Chip


class CollectionQueue(QAbstractListModel):
    def __init__(self, queue=None):
        super(CollectionQueue, self).__init__()
        self.queue = queue or []

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            return self.queue[index.row()]

    def rowCount(self, index):
        return len(self.queue)

    def add_to_queue(self, item):
        self.beginInsertRows(
            QModelIndex(), self.rowCount(QModelIndex()), self.rowCount(QModelIndex())
        )
        self.queue.append(item)
        self.endInsertRows()

    def remove_from_queue(self):
        self.beginResetModel()
        self.queue.clear()
        self.endResetModel()


class CollectionQueueWidget(QWidget):
    def __init__(
        self,
        chip: Chip,
        last_selected: Tuple[int, int],
        collection_parameters: Dict[str, Any],
        status_window: QTextEdit,
    ):
        self.chip = chip
        self.last_selected = last_selected
        self.collection_parameters = collection_parameters
        self.status_window = status_window
        super().__init__()
        self.setLayout(QVBoxLayout())
        self._init_ui()

    def _init_ui(self):
        # Add to queue Button
        self.add_to_queue_button = QPushButton("Add to queue")
        self.add_to_queue_button.clicked.connect(self.add_to_queue)
        self.layout().addWidget(self.add_to_queue_button)

        # Queue list
        self.collection_queue = CollectionQueue()
        self.queue_list = QListView()
        self.queue_list.setModel(self.collection_queue)  # Queue model
        self.layout().addWidget(self.queue_list)

        # Clear queue Button
        self.clear_queue_button = QPushButton("Clear queue")
        self.clear_queue_button.clicked.connect(self.clear_queue)
        self.layout().addWidget(self.clear_queue_button)

        # Collect queue Button
        self.collect_queue_button = QPushButton("Collect queue")
        self.collect_queue_button.clicked.connect(self.collect_queue)
        self.layout().addWidget(self.collect_queue_button)

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
