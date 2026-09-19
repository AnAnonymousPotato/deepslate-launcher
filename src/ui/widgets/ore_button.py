"""
deepslate.ui.widgets.ore_button
Custom Ore UI styled buttons.
"""

from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QCursor

class OreButton(QPushButton):
    """Button styled with 9-slice Ore UI aesthetics with icon spacing."""
    
    def __init__(self, text: str = "", variant: str = "default", parent=None):
        self._raw_text = text
        super().__init__(text, parent)
        self.variant = variant
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        if variant == "accent":
            self.setObjectName("PlayButton")
        elif variant == "warning":
            self.setObjectName("KillButton")
        else:
            self.setObjectName("DefaultButton")

        self._update_text()

    def setText(self, text: str):
        self._raw_text = text
        self._update_text()

    def setIcon(self, icon):
        super().setIcon(icon)
        self._update_text()

    def text(self) -> str:
        return self._raw_text

    def _update_text(self):
        super().setText(self._raw_text)

    def set_variant(self, variant: str):
        self.variant = variant
        if variant == "accent":
            self.setObjectName("PlayButton")
        elif variant == "warning":
            self.setObjectName("KillButton")
        else:
            self.setObjectName("DefaultButton")
        self.style().unpolish(self)
        self.style().polish(self)
