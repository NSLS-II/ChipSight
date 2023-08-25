from qtpy.QtCore import Qt, QAbstractListModel, QModelIndex


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
