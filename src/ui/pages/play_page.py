"""
deepslate.ui.pages.play_page
The main Hero / Play page for Deepslate Launcher.
"""

import os
import math
import random
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QFrame, QCheckBox, QSpacerItem, QSizePolicy, QMessageBox
)
from typing import Optional
from PySide6.QtCore import Qt, Signal, QTimer, QSize, QThread, QPoint
from PySide6.QtGui import (
    QPixmap, QCursor, QPainter, QColor, QBrush, QIcon,
    QLinearGradient, QRadialGradient, QPolygon, QPen
)
from src.bridge.engine import engine
from src.ui.theme import IMAGES_DIR, ICONS_DIR
from ..widgets.ore_button import OreButton
from ..widgets.splash_label import SplashLabel
from ..widgets.update_banner import UpdateBanner
from ..dialogs.download_dialog import DownloadDialog

ORE_ICONS = ICONS_DIR / "ore"

class HeroBannerWidget(QFrame):
    """Hero banner with Minecraft panorama background, foreground isometric block diorama, and ambient embers."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Panel")
        self.setFixedHeight(300)
        self.panorama_pix: Optional[QPixmap] = None
        
        pano_path = IMAGES_DIR / "panorama.png"
        if pano_path.exists():
            self.panorama_pix = QPixmap(str(pano_path))

        # Floating ambient embers
        self.particles_enabled = engine.get_setting("ambient_particles", True)
        self.particles = []
        if self.particles_enabled:
            for _ in range(16):
                self.particles.append(self._spawn_particle(initial=True))
            self.anim_timer = QTimer(self)
            self.anim_timer.timeout.connect(self._tick_particles)
            self.anim_timer.start(33) # ~30 fps
        else:
            self.anim_timer = None

    def _spawn_particle(self, initial=False) -> dict:
        w = max(self.width(), 700)
        is_left = (random.random() < 0.5)
        if is_left:
            px = random.randint(15, 140)
        else:
            px = random.randint(w - 150, w - 15)
        
        py = random.randint(150, 290) if initial else random.randint(250, 295)
        return {
            "x": float(px),
            "y": float(py),
            "size": random.choice([2, 3, 3, 4]),
            "alpha": float(random.randint(130, 240)),
            "speed": random.uniform(0.4, 0.9),
            "drift": random.uniform(-0.4, 0.4),
            "phase": random.uniform(0, 6.28)
        }

    def _tick_particles(self):
        if not self.isVisible() or not self.particles_enabled:
            return
        w = max(self.width(), 700)
        for p in self.particles:
            p["y"] -= p["speed"]
            p["x"] += math.sin(p["phase"]) * 0.4
            p["phase"] += 0.04
            p["alpha"] -= 1.4
            if p["y"] < 130 or p["alpha"] <= 0:
                is_left = (random.random() < 0.5)
                p["x"] = float(random.randint(15, 140) if is_left else random.randint(w - 150, w - 15))
                p["y"] = float(random.randint(260, 295))
                p["alpha"] = float(random.randint(140, 240))
                p["speed"] = random.uniform(0.4, 0.9)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        # 1. Draw panorama scaled
        if self.panorama_pix and not self.panorama_pix.isNull():
            scaled = self.panorama_pix.scaled(
                self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

        # 2. Dark cavern overlay
        painter.fillRect(self.rect(), QColor(16, 17, 18, 160))

        # 3. Isometric block renderer
        def draw_iso_block(ox, oy, size, is_emerald=False, is_bedrock=False):
            w2 = size
            h4 = int(size * 0.5)

            top_pts = [
                QPoint(ox, oy - h4),
                QPoint(ox + w2, oy),
                QPoint(ox, oy + h4),
                QPoint(ox - w2, oy)
            ]
            left_pts = [
                QPoint(ox - w2, oy),
                QPoint(ox, oy + h4),
                QPoint(ox, oy + h4 + size),
                QPoint(ox - w2, oy + size)
            ]
            right_pts = [
                QPoint(ox, oy + h4),
                QPoint(ox + w2, oy),
                QPoint(ox + w2, oy + size),
                QPoint(ox, oy + h4 + size)
            ]

            painter.setPen(Qt.NoPen)
            if is_emerald:
                painter.setBrush(QColor(56, 62, 68))
            elif is_bedrock:
                painter.setBrush(QColor(38, 40, 44))
            else:
                painter.setBrush(QColor(48, 52, 58))
            painter.drawPolygon(QPolygon(top_pts))

            if is_bedrock:
                painter.setBrush(QColor(22, 24, 26))
            else:
                painter.setBrush(QColor(30, 33, 37))
            painter.drawPolygon(QPolygon(left_pts))

            if is_bedrock:
                painter.setBrush(QColor(16, 18, 20))
            else:
                painter.setBrush(QColor(22, 24, 27))
            painter.drawPolygon(QPolygon(right_pts))

            # Deepslate horizontal strata lines
            painter.setPen(QPen(QColor(18, 20, 22, 120), 2))
            painter.drawLine(ox - w2 + 4, oy + int(size * 0.35), ox - 4, oy + h4 + int(size * 0.35))
            painter.drawLine(ox - w2 + 6, oy + int(size * 0.7), ox - 4, oy + h4 + int(size * 0.7))
            painter.drawLine(ox + 4, oy + h4 + int(size * 0.4), ox + w2 - 4, oy + int(size * 0.4))
            painter.drawLine(ox + 4, oy + h4 + int(size * 0.75), ox + w2 - 6, oy + int(size * 0.75))

            # Edge outlines
            painter.setPen(QPen(QColor(14, 15, 17, 200), 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawPolygon(QPolygon(top_pts))
            painter.drawPolygon(QPolygon(left_pts))
            painter.drawPolygon(QPolygon(right_pts))

            if is_emerald:
                painter.setPen(Qt.NoPen)
                # Top gem
                painter.setBrush(QColor(85, 255, 85))
                painter.drawPolygon(QPolygon([
                    QPoint(ox - 2, oy - 4), QPoint(ox + 6, oy),
                    QPoint(ox + 2, oy + 4), QPoint(ox - 6, oy)
                ]))
                painter.setBrush(QColor(168, 248, 154))
                painter.drawPolygon(QPolygon([
                    QPoint(ox - 1, oy - 2), QPoint(ox + 3, oy),
                    QPoint(ox + 1, oy + 2), QPoint(ox - 3, oy)
                ]))
                # Left gem
                painter.setBrush(QColor(35, 98, 18))
                painter.drawPolygon(QPolygon([
                    QPoint(ox - w2 + 8, oy + 10), QPoint(ox - w2 + 20, oy + 14),
                    QPoint(ox - w2 + 18, oy + 26), QPoint(ox - w2 + 6, oy + 22)
                ]))
                painter.setBrush(QColor(85, 255, 85))
                painter.drawPolygon(QPolygon([
                    QPoint(ox - w2 + 10, oy + 12), QPoint(ox - w2 + 18, oy + 15),
                    QPoint(ox - w2 + 16, oy + 23), QPoint(ox - w2 + 8, oy + 20)
                ]))
                painter.setBrush(QColor(168, 248, 154))
                painter.drawPolygon(QPolygon([
                    QPoint(ox - w2 + 12, oy + 14), QPoint(ox - w2 + 15, oy + 15),
                    QPoint(ox - w2 + 14, oy + 19), QPoint(ox - w2 + 11, oy + 18)
                ]))
                # Right gem
                painter.setBrush(QColor(35, 98, 18))
                painter.drawPolygon(QPolygon([
                    QPoint(ox + 6, oy + h4 + 8), QPoint(ox + 18, oy + h4 + 4),
                    QPoint(ox + 20, oy + h4 + 18), QPoint(ox + 8, oy + h4 + 22)
                ]))
                painter.setBrush(QColor(85, 255, 85))
                painter.drawPolygon(QPolygon([
                    QPoint(ox + 8, oy + h4 + 10), QPoint(ox + 16, oy + h4 + 7),
                    QPoint(ox + 18, oy + h4 + 16), QPoint(ox + 10, oy + h4 + 19)
                ]))
                painter.setBrush(QColor(168, 248, 154))
                painter.drawPolygon(QPolygon([
                    QPoint(ox + 10, oy + h4 + 11), QPoint(ox + 14, oy + h4 + 9),
                    QPoint(ox + 15, oy + h4 + 14), QPoint(ox + 11, oy + h4 + 16)
                ]))

        # 4. Bottom shelf depth gradient
        shelf_grad = QLinearGradient(0, self.height() - 80, 0, self.height())
        shelf_grad.setColorAt(0.0, QColor(14, 15, 17, 0))
        shelf_grad.setColorAt(0.5, QColor(14, 15, 17, 140))
        shelf_grad.setColorAt(1.0, QColor(12, 13, 14, 250))
        painter.fillRect(0, self.height() - 80, self.width(), 80, shelf_grad)

        # 5. Draw left isometric block cluster
        draw_iso_block(30, self.height() - 45, 34, is_emerald=True)
        draw_iso_block(72, self.height() - 32, 28, is_emerald=False)
        draw_iso_block(112, self.height() - 18, 26, is_emerald=False)
        draw_iso_block(0, self.height() - 15, 38, is_bedrock=True)
        draw_iso_block(46, self.height() - 8, 32, is_emerald=False)
        draw_iso_block(88, self.height() - 2, 28, is_emerald=True)

        # 6. Draw right isometric block cluster
        draw_iso_block(self.width() - 35, self.height() - 45, 34, is_emerald=True)
        draw_iso_block(self.width() - 78, self.height() - 32, 28, is_emerald=False)
        draw_iso_block(self.width() - 118, self.height() - 18, 26, is_emerald=False)
        draw_iso_block(self.width() - 5, self.height() - 15, 38, is_bedrock=True)
        draw_iso_block(self.width() - 52, self.height() - 8, 32, is_emerald=False)
        draw_iso_block(self.width() - 92, self.height() - 2, 28, is_emerald=True)

        # 7. Draw floating ambient particles (embers)
        if self.particles_enabled:
            painter.setPen(Qt.NoPen)
            for p in self.particles:
                ea = max(0, min(255, int(p["alpha"])))
                ps = p["size"]
                painter.setBrush(QColor(85, 255, 85, ea))
                painter.drawRect(int(p["x"]), int(p["y"]), ps, ps)
                if ps > 2:
                    painter.setBrush(QColor(200, 255, 200, min(255, ea + 30)))
                    painter.drawRect(int(p["x"] + 1), int(p["y"] + 1), ps - 2, ps - 2)

        # 8. Border
        painter.setPen(QPen(QColor(43, 44, 46), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)
        painter.end()


class PlayPage(QWidget):
    """Primary play page with hero banner, version selector, and launch button."""
    
    launch_requested = Signal()
    kill_requested = Signal()
    settings_changed = Signal()
    open_tab_requested = Signal(str)

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
        title_container.setFixedSize(680, 160)

        title_img_path = IMAGES_DIR / "minecraft_title.png"
        if title_img_path.exists():
            title_pix = QPixmap(str(title_img_path)).scaled(400, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            title_label = QLabel(title_container)
            title_label.setPixmap(title_pix)
            title_label.setGeometry(80, 8, 400, 100)
            title_label.setAlignment(Qt.AlignCenter)
        else:
            title_label = QLabel("MINECRAFT", title_container)
            title_label.setObjectName("PageTitle")
            title_label.setGeometry(80, 8, 400, 100)
            title_label.setAlignment(Qt.AlignCenter)

        sub_hero = QLabel("Bedrock Edition for Linux", title_container)
        sub_hero.setStyleSheet("font-size: 13px; font-weight: bold; color: #70B95C; letter-spacing: 1px;")
        sub_hero.setGeometry(80, 112, 400, 24)
        sub_hero.setAlignment(Qt.AlignCenter)

        # Minecraft Splash text anchored at bottom right of the MINECRAFT logo
        self.splash = SplashLabel(title_container)
        self.splash.setGeometry(370, 48, 310, 95)

        hero_layout.addWidget(title_container, alignment=Qt.AlignCenter)
        main_layout.addWidget(hero_frame)

        # 2. Quick Toggles & Feature Cards Bar
        toggles_frame = QFrame()
        toggles_frame.setObjectName("Card")
        toggles_layout = QVBoxLayout(toggles_frame)
        toggles_layout.setContentsMargins(14, 10, 14, 10)
        toggles_layout.setSpacing(10)

        # Row 1: Engine Toggles
        engine_row = QHBoxLayout()
        engine_row.setSpacing(18)

        self.mangohud_cb = QCheckBox("MangoHud")
        self.mangohud_cb.setToolTip("Overlay FPS, frame timings, and hardware metrics")
        self.mangohud_cb.setChecked("MANGOHUD=1" in engine.get_setting("custom_env", ""))
        self.mangohud_cb.toggled.connect(self._on_mangohud_toggled)

        self.rtx_cb = QCheckBox("Ray Tracing (DXR)")
        self.rtx_cb.setToolTip("DirectX Raytracing (DXR 1.1 / Universal VKD3D-Proton)")
        self.rtx_cb.setChecked(engine.get_setting("vkd3d_proton", True))
        self.rtx_cb.toggled.connect(self._on_rtx_toggled)

        self.wayland_cb = QCheckBox("Wayland Driver")
        self.wayland_cb.setToolTip("Experimental native Wayland mouse capture and zero latency")
        self.wayland_cb.setChecked("BOL_INPUT=wayland" in engine.get_setting("custom_env", ""))
        self.wayland_cb.toggled.connect(self._on_wayland_toggled)

        engine_row.addWidget(self.mangohud_cb)
        engine_row.addWidget(self.rtx_cb)
        engine_row.addWidget(self.wayland_cb)
        engine_row.addStretch()
        toggles_layout.addLayout(engine_row)

        # Row 2: Quick Action Ore Buttons
        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)

        ore_dir = ICONS_DIR / "ore"

        # Shaders (BetterRTX) Quick Button
        shaders_btn = OreButton("Shaders (RTX)")
        shaders_icon = ore_dir / "shaderpacks.png"
        if shaders_icon.exists():
            shaders_btn.setIcon(QIcon(str(shaders_icon)))
            shaders_btn.setIconSize(QSize(18, 18))
        shaders_btn.setToolTip("Browse and install BetterRTX ray tracing presets")
        shaders_btn.clicked.connect(lambda: self.open_tab_requested.emit("tools:shaders"))
        actions_row.addWidget(shaders_btn)

        # Backups Quick Button
        backups_btn = OreButton("World Backups")
        backups_icon = ore_dir / "export.png"
        if backups_icon.exists():
            backups_btn.setIcon(QIcon(str(backups_icon)))
            backups_btn.setIconSize(QSize(18, 18))
        backups_btn.setToolTip("View automated world snapshots and backups")
        backups_btn.clicked.connect(lambda: self.open_tab_requested.emit("tools:backups"))
        actions_row.addWidget(backups_btn)

        worlds_btn = OreButton("Worlds Folder")
        worlds_icon = ore_dir / "worlds.png"
        if worlds_icon.exists():
            worlds_btn.setIcon(QIcon(str(worlds_icon)))
            worlds_btn.setIconSize(QSize(18, 18))
        worlds_btn.clicked.connect(lambda: engine.open_mojang_subfolder("minecraftWorlds"))
        actions_row.addWidget(worlds_btn)

        shots_btn = OreButton("Screenshots")
        shots_icon = ore_dir / "screenshots.png"
        if shots_icon.exists():
            shots_btn.setIcon(QIcon(str(shots_icon)))
            shots_btn.setIconSize(QSize(18, 18))
        shots_btn.clicked.connect(lambda: engine.open_mojang_subfolder("Screenshots"))
        actions_row.addWidget(shots_btn)

        actions_row.addStretch()
        toggles_layout.addLayout(actions_row)

        # 2. Update Banner (shown when newer release is available)
        self.update_banner = UpdateBanner(self)
        self.update_banner.update_requested.connect(self._start_easy_update)
        main_layout.addWidget(self.update_banner)

        main_layout.addWidget(toggles_frame)

        # 3. Status Bar with Playtime
        status_box = QHBoxLayout()
        self.status_icon = QLabel()
        self.status_icon.setFixedSize(14, 14)
        self.status_icon.setAlignment(Qt.AlignCenter)
        self._update_status_icon(True)

        self.status_text = QLabel("Ready to play")
        self.status_text.setStyleSheet("font-size: 12px; color: #CCCCCC;")
        status_box.addWidget(self.status_icon)
        status_box.addWidget(self.status_text)
        status_box.addStretch()

        self.playtime_label = QLabel(f"Total Playtime: {engine.get_total_playtime_formatted()}")
        self.playtime_label.setObjectName("MutedText")
        status_box.addWidget(self.playtime_label)

        main_layout.addLayout(status_box)

        # 4. Launch Dock (Minecraft Launcher Control Bar)
        dock = QFrame()
        dock.setObjectName("Card")
        dock.setStyleSheet("QFrame#Card { background-color: #202122; border: 2px solid #303133; padding: 12px; }")
        dock_layout = QHBoxLayout(dock)
        dock_layout.setContentsMargins(14, 10, 14, 10)
        dock_layout.setSpacing(16)

        # Block icon + Version dropdown
        ver_container = QHBoxLayout()
        ver_container.setSpacing(12)

        ver_icon_lbl = QLabel()
        b_icon = ORE_ICONS / "minecraft.png"
        if not b_icon.exists():
            b_icon = ICONS_DIR / "bedrock.png"
        if b_icon.exists():
            ver_icon_lbl.setPixmap(QPixmap(str(b_icon)).scaled(34, 34, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        ver_container.addWidget(ver_icon_lbl)

        ver_box = QVBoxLayout()
        ver_box.setSpacing(2)
        ver_label = QLabel("INSTALLATION")
        ver_label.setObjectName("MutedText")
        self.version_combo = QComboBox()
        self.version_combo.setMinimumWidth(280)
        self.version_combo.currentIndexChanged.connect(self._on_version_selected)
        ver_box.addWidget(ver_label)
        ver_box.addWidget(self.version_combo)
        ver_container.addLayout(ver_box)
        dock_layout.addLayout(ver_container)

        dock_layout.addStretch()

        # Big PLAY / STOP Button
        self.action_button = OreButton("PLAY", variant="accent")
        self.action_button.setFixedWidth(200)
        self.action_button.setFixedHeight(46)
        play_icon = ORE_ICONS / "launch.png"
        if play_icon.exists():
            self.action_button.setIcon(QIcon(str(play_icon)))
            self.action_button.setIconSize(QSize(20, 20))
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
        self.update_banner.check_updates_async()

    def _start_easy_update(self, target_version: str):
        dlg = DownloadDialog(
            edition="release",
            version=target_version,
            display_name=f"Minecraft Bedrock v{target_version}",
            parent=self
        )
        if dlg.exec():
            # Activate the new build
            for b in engine.get_installed_builds():
                if b.get("version") == target_version:
                    engine.set_setting("game_dir", str(b.get("path")))
                    engine.set_setting("mc_version", target_version)
                    if b.get("edition"):
                        engine.set_setting("mc_edition", b.get("edition"))
                    break
            self.refresh_versions()
            self.update_banner.hide()
            QMessageBox.information(
                self,
                "Update Complete",
                f"Successfully updated to Minecraft Bedrock v{target_version}!\n\nYour worlds, player data, and settings remain untouched."
            )

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

    def _update_status_icon(self, online: bool, busy: bool = False):
        if busy:
            icon_path = ICONS_DIR / "status_busy.svg"
        elif online:
            icon_path = ICONS_DIR / "status_online.svg"
        else:
            icon_path = ICONS_DIR / "status_offline.svg"
        if icon_path.exists():
            pix = QPixmap(str(icon_path)).scaled(12, 12, Qt.KeepAspectRatio, Qt.FastTransformation)
            self.status_icon.setPixmap(pix)

    def set_game_running(self, running: bool):
        self.game_running = running
        if running:
            engine.start_session()
            self.action_button.setText("STOP")
            stop_icon = ORE_ICONS / "delete.png"
            if stop_icon.exists():
                self.action_button.setIcon(QIcon(str(stop_icon)))
            self.action_button.set_variant("warning")
            self._update_status_icon(False, busy=True)
            self.status_text.setText("Minecraft is running...")
        else:
            engine.end_session()
            self.action_button.setText("PLAY")
            play_icon = ORE_ICONS / "launch.png"
            if play_icon.exists():
                self.action_button.setIcon(QIcon(str(play_icon)))
            self.action_button.set_variant("accent")
            self._update_status_icon(True)
            self.status_text.setText("Ready to play")
            self.playtime_label.setText(f"Total Playtime: {engine.get_total_playtime_formatted()}")

    def _check_game_running(self):
        is_running = engine.is_game_running()
        if is_running != self.game_running:
            self.set_game_running(is_running)
        elif self.game_running:
            self.playtime_label.setText(
                f"Session: {engine.get_session_playtime_formatted()} | Total: {engine.get_total_playtime_formatted()}"
            )

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
