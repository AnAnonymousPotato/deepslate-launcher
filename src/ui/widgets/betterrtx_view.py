"""
deepslate.ui.widgets.betterrtx_view
BetterRTX Ray Tracing presets browser, installer, and shader manager.
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QLineEdit, QMessageBox, QFileDialog, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QThread, QSize
from PySide6.QtGui import QIcon, QPixmap

from src.bridge.engine import engine
from src.ui.theme import ICONS_DIR
from .ore_button import OreButton

ORE_ICONS = ICONS_DIR / "ore"


class PresetInstallWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, preset):
        super().__init__()
        self.preset = preset

    def run(self):
        try:
            engine.install_betterrtx_preset(self.preset)
            self.finished.emit(True, f"Preset '{self.preset.get('name')}' installed successfully.")
        except Exception as exc:
            self.finished.emit(False, str(exc))


class BetterRTXView(QWidget):
    """BetterRTX community preset browser and ray tracing manager."""

    status_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)

        # 1. Top Status & Control Card
        self.status_card = QFrame()
        self.status_card.setObjectName("Card")
        status_layout = QVBoxLayout(self.status_card)
        status_layout.setContentsMargins(16, 12, 16, 12)
        status_layout.setSpacing(8)

        top_row = QHBoxLayout()
        icon_lbl = QLabel()
        s_icon = ORE_ICONS / "shaderpacks.png"
        if s_icon.exists():
            icon_lbl.setPixmap(QPixmap(str(s_icon)).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        top_row.addWidget(icon_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_lbl = QLabel("BetterRTX Ray Tracing Engine")
        title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFFFFF;")
        
        self.active_status_lbl = QLabel("Checking status…")
        self.active_status_lbl.setObjectName("MutedText")
        title_box.addWidget(title_lbl)
        title_box.addWidget(self.active_status_lbl)
        top_row.addLayout(title_box, 1)

        # Action Buttons
        self.restore_btn = OreButton("Restore Vanilla")
        self.restore_btn.setToolTip("Revert to Mojang vanilla ray tracing shaders")
        self.restore_btn.clicked.connect(self._restore_vanilla)
        top_row.addWidget(self.restore_btn)

        self.import_rtpack_btn = OreButton("Install .rtpack")
        self.import_rtpack_btn.setToolTip("Install a local custom .rtpack shader file")
        self.import_rtpack_btn.clicked.connect(self._browse_rtpack)
        top_row.addWidget(self.import_rtpack_btn)

        self.refresh_btn = OreButton("Refresh")
        ref_icon = ORE_ICONS / "refresh.png"
        if ref_icon.exists():
            self.refresh_btn.setIcon(QIcon(str(ref_icon)))
            self.refresh_btn.setIconSize(QSize(16, 16))
        self.refresh_btn.clicked.connect(self.refresh_presets)
        top_row.addWidget(self.refresh_btn)

        status_layout.addLayout(top_row)
        main_layout.addWidget(self.status_card)

        # 2. Search & Filter Input
        search_box = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter BetterRTX presets by name or author…")
        self.search_input.textChanged.connect(self._filter_presets)
        search_box.addWidget(self.search_input)
        main_layout.addLayout(search_box)

        # 3. Presets Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)
        self.cards_layout.addStretch()

        self.scroll.setWidget(self.cards_container)
        main_layout.addWidget(self.scroll, 1)

        self.all_presets = []
        self.refresh_presets()

    def refresh_presets(self):
        """Fetch presets from bedrock.graphics and update UI."""
        status = engine.get_betterrtx_status()
        installed_uuid = status.get("uuid")
        installed_name = status.get("installed")
        mat_ver = status.get("material_version")

        if installed_name:
            self.active_status_lbl.setText(f"Active Preset: {installed_name} (Material v{mat_ver or '?'})")
            self.active_status_lbl.setStyleSheet("font-size: 11px; color: #70B95C; font-weight: bold;")
            self.restore_btn.setEnabled(True)
        else:
            self.active_status_lbl.setText(f"Vanilla Ray Tracing Shaders (Material v{mat_ver or '?'})")
            self.active_status_lbl.setStyleSheet("font-size: 11px; color: #CCCCCC;")
            self.restore_btn.setEnabled(False)

        self.all_presets = engine.list_betterrtx_presets()
        self._filter_presets(self.search_input.text())

    def _filter_presets(self, query: str = ""):
        # Clear existing cards except spacer
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item:
                w = item.widget()
                if w:
                    w.setParent(None)
                    w.deleteLater()

        q = query.strip().lower()
        status = engine.get_betterrtx_status()
        active_uuid = status.get("uuid")
        active_name = status.get("installed")

        filtered = [
            p for p in self.all_presets
            if not q or q in p.get("name", "").lower() or q in (p.get("author") or "").lower()
        ]

        if not filtered and self.all_presets:
            lbl = QLabel(f"No presets match '{query}'.")
            lbl.setObjectName("MutedText")
            lbl.setAlignment(Qt.AlignCenter)
            self.cards_layout.insertWidget(0, lbl)
            return
        elif not self.all_presets:
            lbl = QLabel("Could not load presets from bedrock.graphics. Check network connection.")
            lbl.setObjectName("MutedText")
            lbl.setAlignment(Qt.AlignCenter)
            self.cards_layout.insertWidget(0, lbl)
            return

        for preset in filtered:
            is_active = (active_uuid and active_uuid == preset.get("uuid")) or (active_name and active_name == preset.get("name"))
            card = self._create_preset_card(preset, is_active)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def _create_preset_card(self, preset: dict, is_active: bool) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(14)

        info = QVBoxLayout()
        info.setSpacing(2)

        name = preset.get("name", "Unnamed Preset")
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        title_lbl = QLabel(name)
        title_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #FFFFFF;")
        title_row.addWidget(title_lbl)

        if is_active:
            badge = QLabel("ACTIVE")
            badge.setObjectName("StatusBadge")
            title_row.addWidget(badge)
        title_row.addStretch()

        author = preset.get("author") or "Community"
        game_ver = preset.get("game_version") or "Latest"
        meta_lbl = QLabel(f"Author: {author}  •  Game Version: {game_ver}")
        meta_lbl.setObjectName("MutedText")

        info.addLayout(title_row)
        info.addWidget(meta_lbl)
        layout.addLayout(info, 1)

        if not is_active:
            apply_btn = OreButton("Apply Preset", variant="accent")
            apply_btn.setMinimumWidth(110)
            apply_btn.clicked.connect(lambda _, p=preset: self._install_preset(p))
            layout.addWidget(apply_btn)
        else:
            in_use_lbl = QLabel("Installed")
            in_use_lbl.setStyleSheet("font-size: 12px; color: #70B95C; font-weight: bold; padding-right: 8px;")
            layout.addWidget(in_use_lbl)

        return card

    def _install_preset(self, preset: dict):
        reply = QMessageBox.question(
            self,
            "Install BetterRTX Preset",
            f"Install '{preset.get('name')}' into your active Minecraft build?\n\nVanilla shaders can be restored at any time.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        self.worker = PresetInstallWorker(preset)
        self.worker.finished.connect(self._on_preset_installed)
        self.worker.start()

    def _on_preset_installed(self, success: bool, message: str):
        if success:
            QMessageBox.information(self, "BetterRTX", message)
            self.refresh_presets()
            self.status_changed.emit()
        else:
            QMessageBox.critical(self, "Installation Failed", f"Could not install BetterRTX preset:\n\n{message}")

    def _browse_rtpack(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select BetterRTX .rtpack File",
            str(Path.home()),
            "BetterRTX Pack (*.rtpack);;All Files (*)"
        )
        if path:
            try:
                engine.install_betterrtx_rtpack(Path(path))
                QMessageBox.information(self, "BetterRTX", f"Successfully installed {Path(path).name}!")
                self.refresh_presets()
                self.status_changed.emit()
            except Exception as exc:
                QMessageBox.critical(self, "Error", f"Failed to install .rtpack:\n\n{exc}")

    def _restore_vanilla(self):
        reply = QMessageBox.question(
            self,
            "Restore Vanilla Shaders",
            "Restore Mojang's original vanilla ray tracing shaders?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                engine.restore_vanilla_shaders()
                QMessageBox.information(self, "BetterRTX", "Vanilla shaders restored successfully!")
                self.refresh_presets()
                self.status_changed.emit()
            except Exception as exc:
                QMessageBox.critical(self, "Error", f"Failed to restore shaders:\n\n{exc}")
