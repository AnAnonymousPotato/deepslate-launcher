"""
deepslate.ui.widgets.world_backups_view
Minecraft Bedrock world saves and automated backup manager.
"""

import os
import time
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap

from src.bridge.engine import engine
from src.ui.theme import ICONS_DIR
from .ore_button import OreButton

ORE_ICONS = ICONS_DIR / "ore"


class WorldBackupsView(QWidget):
    """View managing world saves, automated snapshots, and export archives."""

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)

        # 1. Action & Status Bar
        control_card = QFrame()
        control_card.setObjectName("Card")
        ctrl_layout = QVBoxLayout(control_card)
        ctrl_layout.setContentsMargins(16, 12, 16, 12)
        ctrl_layout.setSpacing(10)

        header_row = QHBoxLayout()
        w_icon = QLabel()
        worlds_img = ORE_ICONS / "worlds.png"
        if worlds_img.exists():
            w_icon.setPixmap(QPixmap(str(worlds_img)).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header_row.addWidget(w_icon)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_lbl = QLabel("World Saves & Snapshot Safety")
        title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFFFFF;")
        desc_lbl = QLabel("Automated safety snapshots prevent world corruption across Bedrock version updates.")
        desc_lbl.setObjectName("MutedText")
        title_box.addWidget(title_lbl)
        title_box.addWidget(desc_lbl)
        header_row.addLayout(title_box, 1)

        self.refresh_btn = OreButton("Refresh")
        ref_icon = ORE_ICONS / "refresh.png"
        if ref_icon.exists():
            self.refresh_btn.setIcon(QIcon(str(ref_icon)))
            self.refresh_btn.setIconSize(QSize(16, 16))
        self.refresh_btn.clicked.connect(self.refresh_backups)
        header_row.addWidget(self.refresh_btn)

        ctrl_layout.addLayout(header_row)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.snap_btn = OreButton("Take Snapshot", variant="accent")
        save_icon = ORE_ICONS / "export.png"
        if save_icon.exists():
            self.snap_btn.setIcon(QIcon(str(save_icon)))
            self.snap_btn.setIconSize(QSize(16, 16))
        self.snap_btn.clicked.connect(self._create_snapshot)
        btn_row.addWidget(self.snap_btn)

        self.copy_preview_btn = OreButton("Copy to Preview")
        self.copy_preview_btn.setToolTip("Copy Release worlds to Minecraft Preview")
        self.copy_preview_btn.clicked.connect(self._copy_to_preview)
        btn_row.addWidget(self.copy_preview_btn)

        self.open_worlds_btn = OreButton("Worlds Folder")
        folder_icon = ORE_ICONS / "viewfolder.png"
        if folder_icon.exists():
            self.open_worlds_btn.setIcon(QIcon(str(folder_icon)))
            self.open_worlds_btn.setIconSize(QSize(16, 16))
        self.open_worlds_btn.clicked.connect(lambda: engine.open_mojang_subfolder("minecraftWorlds"))
        btn_row.addWidget(self.open_worlds_btn)

        self.export_zip_btn = OreButton("Export .zip")
        self.export_zip_btn.setToolTip("Export a standalone .zip backup archive")
        self.export_zip_btn.clicked.connect(self._export_zip)
        btn_row.addWidget(self.export_zip_btn)

        btn_row.addStretch()
        ctrl_layout.addLayout(btn_row)
        main_layout.addWidget(control_card)

        # 2. Backups List Scroll Area
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

        self.refresh_backups()

    def refresh_backups(self):
        """Reload list of backups from BOL saves backend."""
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item:
                w = item.widget()
                if w:
                    w.setParent(None)
                    w.deleteLater()

        backups = engine.list_world_backups()

        if not backups:
            empty_card = QFrame()
            empty_card.setObjectName("Card")
            e_layout = QVBoxLayout(empty_card)
            e_layout.setContentsMargins(20, 24, 20, 24)
            e_layout.setSpacing(8)

            lbl = QLabel("No world snapshots found.")
            lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #FFFFFF;")
            lbl.setAlignment(Qt.AlignCenter)
            e_layout.addWidget(lbl)

            hint = QLabel("Snapshots are automatically created before launching a newer Minecraft version, or you can take one now.")
            hint.setObjectName("MutedText")
            hint.setAlignment(Qt.AlignCenter)
            e_layout.addWidget(hint)

            self.cards_layout.insertWidget(0, empty_card)
            return

        for b in backups:
            card = self._create_backup_card(b)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def _create_backup_card(self, backup: dict) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(14)

        info = QVBoxLayout()
        info.setSpacing(3)

        created_ts = backup.get("created")
        if created_ts:
            time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created_ts))
        else:
            time_str = "Snapshot"

        reason = backup.get("reason") or "Automated backup"
        edition = backup.get("edition") or "release"
        ver = backup.get("version") or "current"

        title_lbl = QLabel(f"{time_str}  •  {reason}")
        title_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #FFFFFF;")

        path_val = backup.get("path")
        meta_lbl = QLabel(f"Edition: {edition}  |  Version: {ver}  |  Location: {path_val}")
        meta_lbl.setObjectName("MutedText")

        info.addWidget(title_lbl)
        info.addWidget(meta_lbl)
        layout.addLayout(info, 1)

        # Actions
        restore_btn = OreButton("Restore Worlds", variant="warning")
        restore_btn.setMinimumWidth(116)
        restore_btn.setToolTip("Restore saved worlds to this snapshot")
        restore_btn.clicked.connect(lambda _, p=path_val: self._restore_snapshot(p, time_str))
        layout.addWidget(restore_btn)

        return card

    def _create_snapshot(self):
        try:
            engine.create_world_backup(reason="Manual Snapshot")
            QMessageBox.information(self, "Backup Created", "World snapshot created successfully!")
            self.refresh_backups()
        except Exception as exc:
            QMessageBox.critical(self, "Backup Failed", f"Could not create snapshot:\n\n{exc}")

    def _restore_snapshot(self, path, time_str):
        reply = QMessageBox.warning(
            self,
            "Confirm World Restore",
            f"Are you sure you want to restore worlds to the snapshot from {time_str}?\n\nAny world progress made after this snapshot will be replaced.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                engine.restore_world_backup(path)
                QMessageBox.information(self, "Restore Complete", f"Successfully restored worlds from snapshot {time_str}!")
            except Exception as exc:
                QMessageBox.critical(self, "Restore Failed", f"Could not restore snapshot:\n\n{exc}")

    def _copy_to_preview(self):
        reply = QMessageBox.question(
            self,
            "Copy Worlds to Preview",
            "Copy all current Release worlds over to Minecraft Preview?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                engine.copy_worlds_to_preview()
                QMessageBox.information(self, "Complete", "Worlds copied to Minecraft Preview successfully!")
            except Exception as exc:
                QMessageBox.critical(self, "Failed", f"Could not copy worlds to preview:\n\n{exc}")

    def _export_zip(self):
        dest_dir = QFileDialog.getExistingDirectory(self, "Select Export Folder", str(Path.home()))
        if dest_dir:
            try:
                out = engine.backup_worlds(Path(dest_dir))
                if out:
                    QMessageBox.information(self, "Export Complete", f"Backup archive saved to:\n\n{out}")
                else:
                    QMessageBox.warning(self, "Export Failed", "Could not locate minecraftWorlds directory to back up.")
            except Exception as exc:
                QMessageBox.critical(self, "Error", f"Failed to export archive:\n\n{exc}")
