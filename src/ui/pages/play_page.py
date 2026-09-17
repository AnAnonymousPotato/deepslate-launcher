"""
deepslate.ui.pages.play_page
The main Hero / Play page for Deepslate Launcher.
"""

import os
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QFrame, QCheckBox, QSpacerItem, QSizePolicy, QMessageBox
)
from typing import Optional
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPixmap, QCursor, QPainter, QColor, QBrush
from src.bridge.engine import engine
from src.ui.theme import IMAGES_DIR
from ..widgets.ore_button import OreButton

class HeroBannerWidget(QFrame):
    """Hero banner with Minecraft panorama background and dark vignette overlay."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Panel")
        self.setFixedHeight(300)
        self.panorama_pix: Optional[QPixmap] = None
        
        pano_path = IMAGES_DIR / "panorama.png"
        if pano_path.exists():
            self.panorama_pix = QPixmap(str(pano_path))

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Draw panorama scaled
        if self.panorama_pix and not self.panorama_pix.isNull():
            scaled = self.panorama_pix.scaled(
                self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            # Center crop
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

        # Dark overlay
        painter.fillRect(self.rect(), QColor(16, 17, 18, 170))

        # Border
        painter.setPen(QColor(43, 44, 46))
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)
        painter.end()


class PlayPage(QWidget):
    """Primary play page with hero banner, version selector, and launch button."""
    
    launch_requested = Signal()
    kill_requested = Signal()
    settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.game_running = False
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(12)
        
        # 1. Hero Banner Frame
        hero_frame = HeroBannerWidget()
        hero_layout = QVBoxLayout(hero_frame)
        hero_layout.setContentsMargins(0, 0, 0, 0)
        
        # Background panorama overlay with Minecraft Bedrock title
        title_container = QWidget()
        title_container_layout = QVBoxLayout(title_container)
        title_container_layout.setAlignment(Qt.AlignCenter)
        
        title_img_path = IMAGES_DIR / "minecraft_title.png"
        if title_img_path.exists():
            title_pix = QPixmap(str(title_img_path)).scaled(420, 110, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            title_label = QLabel()
            title_label.setPixmap(title_pix)
            title_label.setAlignment(Qt.AlignCenter)
            title_container_layout.addWidget(title_label)
        else:
            title_label = QLabel("MINECRAFT")
            title_label.setObjectName("PageTitle")
            title_label.setAlignment(Qt.AlignCenter)
            title_container_layout.addWidget(title_label)

        sub_hero = QLabel("Bedrock Edition for Linux")
        sub_hero.setStyleSheet("font-size: 14px; font-weight: bold; color: #2ECC71; letter-spacing: 1px;")
        sub_hero.setAlignment(Qt.AlignCenter)
        title_container_layout.addWidget(sub_hero)

        hero_layout.addWidget(title_container)
        main_layout.addWidget(hero_frame)

        # 2. Quick Toggles Bar
        toggles_frame = QFrame()
        toggles_frame.setObjectName("Card")
        toggles_layout = QHBoxLayout(toggles_frame)
        toggles_layout.setContentsMargins(14, 8, 14, 8)
        toggles_layout.setSpacing(18)

        self.mangohud_cb = QCheckBox("MangoHud Overlay")
        self.mangohud_cb.setChecked("MANGOHUD=1" in engine.get_setting("custom_env", ""))
        self.mangohud_cb.toggled.connect(self._on_mangohud_toggled)

        self.rtx_cb = QCheckBox("Ray Tracing (DXR 1.1)")
        self.rtx_cb.setChecked(engine.get_setting("vkd3d_proton", True))
        self.rtx_cb.toggled.connect(self._on_rtx_toggled)

        self.wayland_cb = QCheckBox("Wayland Driver (BOL_INPUT=wayland)")
        self.wayland_cb.setChecked("BOL_INPUT=wayland" in engine.get_setting("custom_env", ""))
        self.wayland_cb.toggled.connect(self._on_wayland_toggled)

        toggles_layout.addWidget(self.mangohud_cb)
        toggles_layout.addWidget(self.rtx_cb)
        toggles_layout.addWidget(self.wayland_cb)
        toggles_layout.addStretch()

        main_layout.addWidget(toggles_frame)

        # 3. Status Bar
        status_box = QHBoxLayout()
        self.status_icon = QLabel("●")
        self.status_icon.setStyleSheet("color: #2ECC71; font-size: 13px;")
        self.status_text = QLabel("Ready to play")
        self.status_text.setStyleSheet("font-size: 12px; color: #CCCCCC;")
        status_box.addWidget(self.status_icon)
        status_box.addWidget(self.status_text)
        status_box.addStretch()
        main_layout.addLayout(status_box)

        # 4. Launch Dock (Minecraft Launcher Control Bar)
        dock = QFrame()
        dock.setObjectName("Card")
        dock.setStyleSheet("QFrame#Card { background-color: #202122; border: 2px solid #303133; padding: 12px; }")
        dock_layout = QHBoxLayout(dock)
        dock_layout.setContentsMargins(14, 10, 14, 10)
        dock_layout.setSpacing(16)

        # Version dropdown
        ver_box = QVBoxLayout()
        ver_box.setSpacing(2)
        ver_label = QLabel("INSTALLATION")
        ver_label.setObjectName("MutedText")
        self.version_combo = QComboBox()
        self.version_combo.setMinimumWidth(260)
        self.version_combo.currentIndexChanged.connect(self._on_version_selected)
        ver_box.addWidget(ver_label)
        ver_box.addWidget(self.version_combo)
        dock_layout.addLayout(ver_box)

        dock_layout.addStretch()

        # Big PLAY / STOP Button
        self.action_button = OreButton("PLAY", variant="accent")
        self.action_button.setFixedWidth(200)
        self.action_button.setFixedHeight(46)
        self.action_button.clicked.connect(self._on_action_clicked)
        dock_layout.addWidget(self.action_button)

        main_layout.addWidget(dock)
        main_layout.addStretch()

        # Refresh versions and state
        self.refresh_versions()
        
        # Periodic check for game status
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._check_game_running)
        self.timer.start(1000)

    def refresh_versions(self):
        """Populate the version selector with locally installed builds."""
        self.version_combo.blockSignals(True)
        self.version_combo.clear()
        
        builds = engine.get_installed_builds()
        cur_game_dir = engine.get_setting("game_dir", "")
        
        selected_index = 0
        for idx, build in enumerate(builds):
            ver = build.get("version", "Unknown")
            name = build.get("name", "Minecraft")
            size_mb = (build.get("size") or 0) / (1024 * 1024)
            label = f"{name} {ver} ({size_mb:.0f} MB)"
            self.version_combo.addItem(label, userData=build)
            
            if str(build.get("path")) == cur_game_dir:
                selected_index = idx

        if builds:
            self.version_combo.setCurrentIndex(selected_index)
            self.action_button.setEnabled(True)
            self.status_text.setText("Ready to play")
        else:
            self.version_combo.addItem("No build installed")
            self.action_button.setEnabled(False)
            self.status_text.setText("Please install a build from the Installations tab.")

        self.version_combo.blockSignals(False)

    def _on_version_selected(self, index: int):
        build = self.version_combo.currentData()
        if build and "path" in build:
            engine.set_setting("game_dir", str(build["path"]))
            engine.set_setting("mc_version", build.get("version"))
            if build.get("edition"):
                engine.set_setting("mc_edition", build.get("edition"))

    def _on_action_clicked(self):
        if self.game_running:
            self.kill_requested.emit()
            engine.kill_game()
            self.set_game_running(False)
        else:
            ready, msg = engine.check_launch_readiness()
            if not ready and msg:
                QMessageBox.warning(self, "Launch Warning", msg)
                return
            self.set_game_running(True)
            self.launch_requested.emit()

    def set_game_running(self, running: bool):
        self.game_running = running
        if running:
            self.action_button.setText("STOP")
            self.action_button.set_variant("warning")
            self.status_icon.setStyleSheet("color: #E67E22; font-size: 13px;")
            self.status_text.setText("Minecraft is running...")
        else:
            self.action_button.setText("PLAY")
            self.action_button.set_variant("accent")
            self.status_icon.setStyleSheet("color: #2ECC71; font-size: 13px;")
            self.status_text.setText("Ready to play")

    def _check_game_running(self):
        is_running = engine.is_game_running()
        if is_running != self.game_running:
            self.set_game_running(is_running)

    def _on_mangohud_toggled(self, checked: bool):
        env = engine.get_setting("custom_env", "")
        parts = [p for p in env.split() if not p.startswith("MANGOHUD=")]
        if checked:
            parts.append("MANGOHUD=1")
        engine.set_setting("custom_env", " ".join(parts).strip())
        self.settings_changed.emit()

    def _on_rtx_toggled(self, checked: bool):
        engine.set_setting("vkd3d_proton", checked)
        self.settings_changed.emit()

    def _on_wayland_toggled(self, checked: bool):
        env = engine.get_setting("custom_env", "")
        parts = [p for p in env.split() if not p.startswith("BOL_INPUT=")]
        if checked:
            parts.append("BOL_INPUT=wayland")
        engine.set_setting("custom_env", " ".join(parts).strip())
        self.settings_changed.emit()
