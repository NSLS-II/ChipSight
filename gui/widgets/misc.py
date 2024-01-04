from qtpy.QtWidgets import QLabel, QWidget
from qtpy.QtGui import QColor, QPainter, QBrush
from qtpy.QtCore import Qt


class LedIndicator(QLabel):
    def __init__(self, parent=None):
        super(LedIndicator, self).__init__(parent)
        self.setFixedSize(20, 20)  # Set the size of the LED
        self.state = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Color based on state
        color = QColor(Qt.green) if self.state else QColor(Qt.red)

        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, self.width(), self.height())  # Draw circle

    def setState(self, state: bool):
        self.state = state
        self.update()  # This will trigger a repaint

class DetectorDistanceWidget(QWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
        websocket_client: "WebSocketClient | None" = None,
    ) -> None:
        super().__init__(parent)
        self.websocket_client = websocket_client
        label = QLabel("Detector Distance")
        self.detector_dist_spin_box = QSpinBox()
        self.detector_dist_spin_box.setValue(10)
        self.detector_dist_spin_box.setMaximum(100)
        self.detector_dist_spin_box.setMinimum(0)