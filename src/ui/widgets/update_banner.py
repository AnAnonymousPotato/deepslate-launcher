"""
deepslate.ui.widgets.update_banner
Prominent Ore UI styled banner notifying players when a newer Minecraft Bedrock release is available.
"""

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QWidget
)
from PySide6.QtCore import Qt, Signal, QSize, QThread
from PySide6.QtGui import QIcon, QPixmap

from src.bridge.engine import engine
from src.ui.theme import ICONS_DIR
from .ore_button import OreButton


class UpdateCheckWorker(QThread):
    result_ready = Signal(bool, str, str, str, str)

    def __init__(self, refresh=False):
        super().__init__()
        self.refresh = refresh

    def run(self):
        res = engine.check_for_game_update("release", refresh=self.refresh)
        self.result_ready.emit(*res)


class UpdateBanner(QFrame):
    """Notification banner alerting player of a newer stable Minecraft version."""

    update_requested = Signal(str)  # Emits target version
    dismissed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("UpdateBanner")
        self.latest_version = ""
        self.latest_display = ""
        
        self.setStyleSheet("""
            QFrame#UpdateBanner {
                background-color: #152213;
                border: 2px solid #3B8526;
                border-radius: 0px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(14)

        # Left Pixel Icon (using Ore UI packages or new icon)
        self.icon_label = QLabel()
        new_icon = ICONS_DIR / "ore" / "new.png"
        if not new_icon.exists():
            new_icon = ICONS_DIR / "app_icon.png"
        if new_icon.exists():
            pix = QPixmap(str(new_icon)).scaled(24, 24, Qt.KeepAspectRatio, Qt.FastTransformation)
            self.icon_label.setPixmap(pix)
        layout.addWidget(self.icon_label)

        # Middle Notice Info
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        self.title_label = QLabel("MINECRAFT UPDATE AVAILABLE")
        self.title_label.setStyleSheet("font-family: \"Mojangles\", sans-serif; font-size: 11px; font-weight: bold; color: #70B95C; letter-spacing: 0.5px;")

        self.detail_label = QLabel()
        self.detail_label.setStyleSheet("font-family: \"Mojangles\", sans-serif; font-size: 11px; color: #E0E0E0;")
        
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.detail_label)
        layout.addLayout(text_layout, 1)

        # Right Action Buttons
        self.update_btn = OreButton("Update Now", variant="accent")
        ref_icon = ICONS_DIR / "ore" / "launch.png"
        if ref_icon.exists():
            self.update_btn.setIcon(QIcon(str(ref_icon)))
            self.update_btn.setIconSize(QSize(16, 16))
        self.update_btn.clicked.connect(self._on_update_clicked)
        layout.addWidget(self.update_btn)

        self.dismiss_btn = OreButton("Later")
        self.dismiss_btn.clicked.connect(self._on_dismiss_clicked)
        layout.addWidget(self.dismiss_btn)

        self.hide()  # Hidden until update detected

    def set_update_info(self, latest_ver: str, latest_disp: str, current_ver: str, current_disp: str):
        self.latest_version = latest_ver
        self.latest_display = latest_disp
        self.detail_label.setText(
            f"Release v{latest_ver} ({latest_disp}) is available. You are on v{current_ver} ({current_disp})."
        )
        self.show()

    def check_updates_async(self, refresh: bool = False):
        self._worker = UpdateCheckWorker(refresh=refresh)
        self._worker.result_ready.connect(self._on_check_result)
        self._worker.start()

    def _on_check_result(self, has_update: bool, latest_ver: str, latest_disp: str, cur_ver: str, cur_disp: str):
        if has_update and latest_ver and cur_ver:
            self.set_update_info(latest_ver, latest_disp or latest_ver, cur_ver, cur_disp or cur_ver)
        else:
            self.hide()

    def _on_update_clicked(self):
        if self.latest_version:
            self.update_requested.emit(self.latest_version)

    def _on_dismiss_clicked(self):
        self.hide()
        self.dismissed.emit()
