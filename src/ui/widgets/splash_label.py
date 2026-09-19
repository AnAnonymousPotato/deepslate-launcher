"""
deepslate.ui.widgets.splash_label
Authentic angled Minecraft yellow splash text with subtle pulse animation.
"""

import random
import math
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QPainter, QFont, QColor, QTransform, QCursor

SPLASHES = [
    "Runs on Linux!",
    "100% Deepslate!",
    "Wayland Native!",
    "Don't dig straight down!",
    "Proton Powered!",
    "Ore UI Inside!",
    "Also try Java Edition!",
    "Bedrock on Wayland!",
    "Mining to Bedrock!",
    "No more ugly GUIs!",
    "Caelestia Approved!",
    "Check out the caves!",
    "Ray Tracing Ready!",
    "Press F3... wait, Bedrock!",
    "Powered by PySide6!",
    "Emerald accents!",
    "Watch out for Creepers!",
    "Now with 9-Slice Vectors!",
    "Diamond swords ready!",
    "Zero AUR maintenance!",
    "Smooth 144 FPS!",
    "MANGOHUD=1",
    "Sleep in a bed to skip night!",
    "Eat some golden apples!",
    "Whispering Bedrock...",
    "Built for Linux gamers!",
    "Crafting since 2011!",
    "Slicker than obsidian!",
    "Arch Linux approved!",
]

class SplashLabel(QWidget):
    """Bouncing, angled yellow Minecraft splash text."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.text = random.choice(SPLASHES)
        self.setFixedSize(300, 60)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setToolTip("Click for another splash!")

        self.phase = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(50) # 20 fps pulse

    def _animate(self):
        self.phase += 0.12
        if self.phase > 2 * math.pi:
            self.phase -= 2 * math.pi
        self.update()

    def mousePressEvent(self, event):
        old = self.text
        choices = [s for s in SPLASHES if s != old]
        self.text = random.choice(choices)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        # Pulse scale calculation
        scale = 1.0 + 0.06 * math.sin(self.phase)

        # Center coordinates
        cx = self.width() / 2.0
        cy = self.height() / 2.0

        transform = QTransform()
        transform.translate(cx, cy)
        transform.rotate(-20.0)
        transform.scale(scale, scale)
        transform.translate(-cx, -cy)
        painter.setTransform(transform)

        font = QFont("Mojangles", 11)
        font.setStyleStrategy(QFont.NoAntialias)
        font.setBold(True)
        painter.setFont(font)

        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(self.text)
        th = fm.ascent()

        tx = int(cx - tw / 2.0)
        ty = int(cy + th / 3.0)

        # Draw drop shadow (#3F3F00)
        painter.setPen(QColor(63, 63, 0))
        painter.drawText(tx + 2, ty + 2, self.text)

        # Draw bright yellow text (#FFFF55)
        painter.setPen(QColor(255, 255, 85))
        painter.drawText(tx, ty, self.text)

        painter.end()
