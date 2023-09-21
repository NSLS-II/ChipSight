from typing import Optional, Dict, Any, TYPE_CHECKING
from qtpy.QtWidgets import (
    QAction,
    QColorDialog,
    QGraphicsScene,
    QGroupBox,
    QFormLayout,
    QHBoxLayout,
    QSpinBox,
    QLabel,
)
from qtpy.QtCore import QPoint, Qt, QRect, QRectF
from qtpy.QtGui import QColor, QPen
from .base_plugin import BasePlugin
from qtpy.QtGui import QMouseEvent
from collections import defaultdict

if TYPE_CHECKING:
    from microscope.microscope import Microscope


class C2CPlugin(BasePlugin):
    """ A plugin to implement click to center
    """

    def __init__(self, parent: "Optional[Microscope]" = None):
        self.name = "Click to center"
        self.updates_image = False
        self.parent = parent

    def mouse_press_event(self, event: QMouseEvent):
        print(f"clicked {event.pos().x()} {event.pos().y()}")

