"""
deepslate.ui.pages.installations_page
Installations and versions manager page.
"""

import os
import subprocess
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QMessageBox, QDialog, QComboBox, QCheckBox,
    QProgressBar, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QCursor

from src.bridge.engine import engine
from ..widgets.ore_button import OreButton

class DownloadWorker(QThread):
    progress = Signal(int, int) # done, total
    finished = Signal(bool, str)

    def __init__(self, edition: str, version: str, force: bool):
        super().__init__()
        self.edition = edition
        self.version = version
        self.force = force

    def run(self):
        try:
            def _cb(done, total):
                self.progress.emit(int(done or 0), int(total or 0))

            engine.install_build(
                edition=self.edition,
                version=self.version if self.version != "latest" else None,
                force=self.force,
                progress_cb=_cb
            )
            self.finished.emit(True, "Installation complete.")
        except Exception as exc:
            self.finished.emit(False, str(exc))


class InstallationsPage(QWidget):
    """Page managing installed and remote Minecraft Bedrock versions."""
    
    version_activated = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(12)
        
        # Header Bar
        header = QHBoxLayout()
        title = QLabel("INSTALLATIONS")
        title.setObjectName("PageTitle")
        header.addWidget(title)
        header.addStretch()

        self.refresh_btn = OreButton("↻ Refresh")
        self.refresh_btn.clicked.connect(self.populate_builds)
        header.addWidget(self.refresh_btn)

        self.new_install_btn = OreButton("+ New Installation", variant="accent")
        self.new_install_btn.clicked.connect(self._show_install_dialog)
        header.addWidget(self.new_install_btn)

        main_layout.addLayout(header)

        # Scroll Area for Build Cards
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)
        self.cards_layout.addStretch()

        self.scroll.setWidget(self.cards_container)
        main_layout.addWidget(self.scroll)

        self.populate_builds()

    def populate_builds(self):
        """Clear and repopulate the list of installed builds."""
        # Clear existing cards except spacer
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        builds = engine.get_installed_builds()
        cur_game_dir = engine.get_setting("game_dir", "")

        for build in builds:
            card = self._create_build_card(build, cur_game_dir)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def _create_build_card(self, build: dict, cur_game_dir: str) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(14)

        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        ver = build.get("version", "Unknown")
        name = build.get("name", "Minecraft")
        size_bytes = build.get("size") or 0
        size_gb = size_bytes / (1024 * 1024 * 1024)
        
        is_active = (str(build.get("path")) == cur_game_dir)

        title_box = QHBoxLayout()
        title_box.setSpacing(8)
        
        title_lbl = QLabel(f"{name}  v{ver}")
        title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFFFFF;")
        title_box.addWidget(title_lbl)

        if is_active:
            badge = QLabel("ACTIVE")
            badge.setObjectName("StatusBadge")
            title_box.addWidget(badge)
        title_box.addStretch()

        path_lbl = QLabel(str(build.get("path", "")))
        path_lbl.setObjectName("MutedText")
        
        size_lbl = QLabel(f"Size: {size_gb:.2f} GiB")
        size_lbl.setStyleSheet("font-size: 11px; color: #A0A0A0;")

        info_layout.addLayout(title_box)
        info_layout.addWidget(path_lbl)
        info_layout.addWidget(size_lbl)
        layout.addLayout(info_layout, 1)

        # Action Buttons
        if not is_active:
            use_btn = OreButton("Use This")
            use_btn.clicked.connect(lambda _, b=build: self._activate_build(b))
            layout.addWidget(use_btn)

        folder_btn = OreButton("Folder")
        folder_btn.clicked.connect(lambda _, p=build.get("path"): self._open_folder(p))
        layout.addWidget(folder_btn)

        del_btn = OreButton("Delete", variant="warning")
        del_btn.clicked.connect(lambda _, b=build: self._delete_build(b))
        layout.addWidget(del_btn)

        return card

    def _activate_build(self, build: dict):
        engine.set_setting("game_dir", str(build.get("path")))
        engine.set_setting("mc_version", build.get("version"))
        if build.get("edition"):
            engine.set_setting("mc_edition", build.get("edition"))
        self.populate_builds()
        self.version_activated.emit(build.get("version", ""))

    def _open_folder(self, path):
        if path and os.path.exists(path):
            subprocess.Popen(["xdg-open", str(path)])

    def _delete_build(self, build: dict):
        ver = build.get("version")
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete Minecraft {ver}?\n\nWorlds and settings will not be affected.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            freed = engine.remove_version(str(build.get("path")))
            QMessageBox.information(self, "Deleted", f"Successfully freed {freed / (1024*1024):.0f} MB.")
            self.populate_builds()

    def _show_install_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Install Minecraft Bedrock")
        dlg.setFixedWidth(420)
        
        dlg_layout = QVBoxLayout(dlg)
        dlg_layout.setContentsMargins(18, 18, 18, 18)
        dlg_layout.setSpacing(12)

        dlg_layout.addWidget(QLabel("Select Edition:"))
        edition_combo = QComboBox()
        edition_combo.addItems(["release", "preview"])
        dlg_layout.addWidget(edition_combo)

        dlg_layout.addWidget(QLabel("Version (or 'latest'):"))
        ver_combo = QComboBox()
        ver_combo.addItem("latest")
        dlg_layout.addWidget(ver_combo)

        force_cb = QCheckBox("Force Re-download / Rebuild")
        dlg_layout.addWidget(force_cb)

        # Progress
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.hide()
        dlg_layout.addWidget(progress_bar)

        status_lbl = QLabel("")
        status_lbl.setObjectName("MutedText")
        dlg_layout.addWidget(status_lbl)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        cancel_btn = OreButton("Cancel")
        cancel_btn.clicked.connect(dlg.reject)
        btn_box.addWidget(cancel_btn)

        start_btn = OreButton("Download & Install", variant="accent")
        btn_box.addWidget(start_btn)
        dlg_layout.addLayout(btn_box)

        # Worker handling
        worker = [None]

        def _on_start():
            edition = edition_combo.currentText()
            version = ver_combo.currentText()
            force = force_cb.isChecked()
            
            progress_bar.show()
            progress_bar.setValue(0)
            status_lbl.setText("Starting download...")
            start_btn.setEnabled(False)
            cancel_btn.setEnabled(False)

            worker[0] = DownloadWorker(edition, version, force)
            
            def _on_progress(done, total):
                if total > 0:
                    pct = int((done / total) * 100)
                    progress_bar.setValue(pct)
                    status_lbl.setText(f"Downloading: {pct}% ({done / (1024*1024):.1f} / {total / (1024*1024):.1f} MB)")
                else:
                    progress_bar.setRange(0, 0)
                    status_lbl.setText("Processing packages...")

            def _on_finish(success, message):
                start_btn.setEnabled(True)
                cancel_btn.setEnabled(True)
                if success:
                    QMessageBox.information(dlg, "Success", "Minecraft installation finished successfully!")
                    dlg.accept()
                    self.populate_builds()
                else:
                    QMessageBox.critical(dlg, "Installation Failed", message)

            worker[0].progress.connect(_on_progress)
            worker[0].finished.connect(_on_finish)
            worker[0].start()

        start_btn.clicked.connect(_on_start)
        dlg.exec()
