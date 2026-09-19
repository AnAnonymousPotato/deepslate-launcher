"""
deepslate.ui.pages.settings_page
Settings management page with General, Graphics/Engine, and Storage tabs.
"""

import os
import subprocess
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QCheckBox, QLineEdit, QFrame, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor

from src.bridge.engine import engine
from ..widgets.ore_button import OreButton

class SettingsPage(QWidget):
    """Configuration interface for launcher and Bedrock runtime."""
    
    settings_saved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(12)
        
        title = QLabel("SETTINGS")
        title.setObjectName("PageTitle")
        main_layout.addWidget(title)

        # Tabbed settings
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_general_tab(), "General")
        self.tabs.addTab(self._build_graphics_tab(), "Graphics + Engine")
        self.tabs.addTab(self._build_storage_tab(), "Storage")
        
        main_layout.addWidget(self.tabs)

    def _build_general_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # 1. Behavior
        b_hdr = QLabel("Behavior")
        b_hdr.setObjectName("SectionHeader")
        layout.addWidget(b_hdr)

        self.close_on_launch_cb = QCheckBox("Close Deepslate Launcher when Minecraft starts")
        self.close_on_launch_cb.setChecked(engine.get_setting("close_on_launch", False))
        self.close_on_launch_cb.toggled.connect(lambda v: engine.set_setting("close_on_launch", v))
        layout.addWidget(self.close_on_launch_cb)

        self.show_betas_cb = QCheckBox("Show Bedrock Preview and Beta editions")
        self.show_betas_cb.setChecked(engine.get_setting("show_betas", True))
        self.show_betas_cb.toggled.connect(lambda v: engine.set_setting("show_betas", v))
        layout.addWidget(self.show_betas_cb)

        self.controller_cb = QCheckBox("Enable Controller / Gamepad navigation in launcher")
        self.controller_cb.setChecked(engine.get_setting("controller_nav", True))
        self.controller_cb.toggled.connect(lambda v: engine.set_setting("controller_nav", v))
        layout.addWidget(self.controller_cb)

        # 2. Integrations
        i_hdr = QLabel("Integrations")
        i_hdr.setObjectName("SectionHeader")
        layout.addWidget(i_hdr)

        self.discord_cb = QCheckBox("Discord Rich Presence")
        self.discord_cb.setChecked(engine.get_setting("discord_presence", True))
        self.discord_cb.toggled.connect(lambda v: engine.set_setting("discord_presence", v))
        layout.addWidget(self.discord_cb)

        self.xbox_friends_cb = QCheckBox("Xbox Live Friends presence")
        self.xbox_friends_cb.setChecked(engine.get_setting("xbox_friends", True))
        self.xbox_friends_cb.toggled.connect(lambda v: engine.set_setting("xbox_friends", v))
        layout.addWidget(self.xbox_friends_cb)

        # 3. Environment Variables
        e_hdr = QLabel("Custom Environment Variables")
        e_hdr.setObjectName("SectionHeader")
        layout.addWidget(e_hdr)

        env_hint = QLabel("Passed to Wine/Proton when launching (e.g. MANGOHUD=1 DXVK_HUD=fps)")
        env_hint.setObjectName("MutedText")
        layout.addWidget(env_hint)

        self.env_edit = QLineEdit()
        self.env_edit.setText(engine.get_setting("custom_env", ""))
        self.env_edit.textChanged.connect(lambda t: engine.set_setting("custom_env", t.strip()))
        layout.addWidget(self.env_edit)

        layout.addStretch()
        return widget

    def _build_graphics_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        g_hdr = QLabel("Engine and Graphics")
        g_hdr.setObjectName("SectionHeader")
        layout.addWidget(g_hdr)

        self.rtx_cb = QCheckBox("Enable Ray Tracing (DirectX 12 / Universal VKD3D-Proton)")
        self.rtx_cb.setChecked(engine.get_setting("vkd3d_proton", True))
        self.rtx_cb.toggled.connect(lambda v: engine.set_setting("vkd3d_proton", v))
        layout.addWidget(self.rtx_cb)

        self.wayland_cb = QCheckBox("Use Experimental Native Wayland Driver (BOL_INPUT=wayland)")
        self.wayland_cb.setChecked("BOL_INPUT=wayland" in engine.get_setting("custom_env", ""))
        self.wayland_cb.toggled.connect(self._on_wayland_toggled)
        layout.addWidget(self.wayland_cb)

        # GPU Safety
        gpu_hdr = QLabel("GPU Crash Safety Barrier")
        gpu_hdr.setObjectName("SectionHeader")
        layout.addWidget(gpu_hdr)

        has_crash = engine.has_gpu_crash_marker()
        self.gpu_status_lbl = QLabel(
            "⚠️ GPU crash detected from a previous run. Launching may be blocked." if has_crash
            else "[OK] Graphics driver state is healthy."
        )
        self.gpu_status_lbl.setStyleSheet("color: #E67E22;" if has_crash else "color: #70B95C;")
        layout.addWidget(self.gpu_status_lbl)

        ack_btn = OreButton("Acknowledge and Clear GPU Crash Marker")
        ack_btn.clicked.connect(self._on_ack_gpu)
        layout.addWidget(ack_btn)

        layout.addStretch()
        return widget

    def _build_storage_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        s_hdr = QLabel("Data and Storage Location")
        s_hdr.setObjectName("SectionHeader")
        layout.addWidget(s_hdr)

        loc_label = QLabel(f"Storage Path: {Path.home() / '.local' / 'share' / 'bedrock-on-linux'}")
        loc_label.setStyleSheet("font-family: monospace; font-size: 12px; color: #FFFFFF;")
        layout.addWidget(loc_label)

        btn_row = QHBoxLayout()
        open_folder_btn = OreButton("Open Storage Folder")
        open_folder_btn.clicked.connect(lambda: subprocess.Popen(["xdg-open", str(Path.home() / ".local" / "share" / "bedrock-on-linux")]))
        btn_row.addWidget(open_folder_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addStretch()
        return widget

    def _on_wayland_toggled(self, checked: bool):
        env = engine.get_setting("custom_env", "")
        parts = [p for p in env.split() if not p.startswith("BOL_INPUT=")]
        if checked:
            parts.append("BOL_INPUT=wayland")
        engine.set_setting("custom_env", " ".join(parts).strip())

    def _on_ack_gpu(self):
        engine.ack_gpu_crash()
        self.gpu_status_lbl.setText("[OK] GPU crash marker cleared.")
        self.gpu_status_lbl.setStyleSheet("color: #2ECC71;")
        QMessageBox.information(self, "Cleared", "GPU safety marker cleared successfully.")
