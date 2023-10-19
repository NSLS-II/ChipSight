from typing import Any, Dict, List, Tuple

from qtpy.QtCore import QAbstractListModel, QModelIndex, Qt
from qtpy.QtWidgets import QListView, QPushButton, QTextEdit, QVBoxLayout, QWidget, QHBoxLayout

from model.chip import Chip
from model.comm_protocol import (
    ClearQueue,
    CollectNeighborhood,
    CollectQueue,
    CollectRow,
)

from .utils import (
    create_add_to_queue_request,
    create_execute_action_request,
    send_message_to_server,
)
from .websocket_client import WebSocketClient


class CollectionQueue(QAbstractListModel):
    def __init__(self, queue=None):
        super(CollectionQueue, self).__init__()
        self.queue: List[CollectRow | CollectNeighborhood] = queue or []

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            return self.queue[index.row()].location

    def rowCount(self, index):
        return len(self.queue)

    def add_to_queue(self, item):
        self.beginInsertRows(
            QModelIndex(), self.rowCount(QModelIndex()), self.rowCount(QModelIndex())
        )
        self.queue.append(item)
        self.endInsertRows()

    def clear_queue(self):
        self.beginResetModel()
        self.queue.clear()
        self.endResetModel()

    def removeRow(self, row: int) -> bool:
        self.beginRemoveRows(QModelIndex(), self.rowCount(row), self.rowCount(row))
        self.queue.pop(row)
        self.endRemoveRows()
        return True


class CollectionQueueWidget(QWidget):
    def __init__(
        self,
        chip: Chip,
        last_selected: Tuple[int, int],
        collection_parameters: Dict[str, Any],
        status_window: QTextEdit,
        websocket_client: WebSocketClient,
    ):
        self.chip = chip
        self.last_selected = last_selected
        self.collection_parameters = collection_parameters
        self.status_window = status_window
        self.websocket_client = websocket_client
        super().__init__()
        self.setLayout(QVBoxLayout())
        self._init_ui()

    def _init_ui(self):
        button_layout = QHBoxLayout()
        # Add to queue Button
        self.add_to_queue_button = QPushButton("Add to queue")
        self.add_to_queue_button.clicked.connect(self.add_to_queue)
        button_layout.addWidget(self.add_to_queue_button)
        self.layout().addLayout(button_layout)

        # Queue list
        self.collection_queue = CollectionQueue()
        self.queue_list = QListView()
        self.queue_list.setModel(self.collection_queue)  # Queue model
        self.layout().addWidget(self.queue_list)

        # Clear queue Button
        self.clear_queue_button = QPushButton("Clear queue")
        self.clear_queue_button.clicked.connect(self.clear_queue)
        button_layout.addWidget(self.clear_queue_button)

        # Collect queue Button
        self.collect_queue_button = QPushButton("Collect queue")
        self.collect_queue_button.clicked.connect(self.collect_queue)
        button_layout.addWidget(self.collect_queue_button)

    def set_last_selected(self, last_selected: Tuple[int, int]):
        self.last_selected = last_selected

    # Add selected blocks and rows to queue
    def add_to_queue(self):
        last_block = self.chip.blocks[self.last_selected[0]][self.last_selected[1]]
        selected_rows = [row for row in last_block.rows if row.selected]
        wait_time = int(self.collection_parameters["exposure_time"]["widget"].text())
        if selected_rows:  # last selected block contains selected rows
            for row in selected_rows:
                row.queued = "queued"
                send_message_to_server(
                    self.websocket_client,
                    create_add_to_queue_request(
                        CollectRow(
                            location=row.address,
                            wait_time=wait_time,
                        ),
                        client_id=self.websocket_client.uuid,
                    ),
                )

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

                        send_message_to_server(
                            self.websocket_client,
                            create_add_to_queue_request(
                                CollectNeighborhood(
                                    location=block.address, wait_time=wait_time
                                ),
                                client_id=self.websocket_client.uuid,
                            ),
                        )
        self.update()

    # Clear the queue
    def clear_queue(self):
        send_message_to_server(
            self.websocket_client,
            create_execute_action_request(
                ClearQueue(), client_id=self.websocket_client.uuid
            ),
        )
        for block_row in self.chip.blocks:
            for block in block_row:
                block.queued = "not queued"
                for row in block.rows:
                    row.queued = "not queued"
        self.collection_queue.clear_queue()
        self.update()

    def collect_queue(self):
        send_message_to_server(
            self.websocket_client,
            create_execute_action_request(
                CollectQueue(), client_id=self.websocket_client.uuid
            ),
        )
        while self.collection_queue.queue:
            container_address = self.collection_queue.queue.pop(0)
            if isinstance(container_address, CollectNeighborhood):  # it's a block
                self.collect_block(container_address)
            else:  # it's a row
                self.collect_row(container_address)
        self.update()

    def collect_row(self, data: CollectRow):
        row_address = data.location
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

    def collect_block(self, data: CollectNeighborhood):
        block_address = data.location
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
