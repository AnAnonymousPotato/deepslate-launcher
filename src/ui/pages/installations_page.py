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
    QProgressBar, QSizePolicy, QLineEdit, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal, QThread, QSize
from PySide6.QtGui import QCursor, QIcon, QColor

from src.bridge.engine import engine
from src.ui.theme import ICONS_DIR
from ..widgets.ore_button import OreButton
from ..widgets.update_banner import UpdateBanner
from ..dialogs.download_dialog import DownloadDialog, DownloadWorker

ORE_ICONS = ICONS_DIR / "ore"


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

        self.refresh_btn = OreButton("Refresh")
        ref_icon = ORE_ICONS / "refresh.png"
        if ref_icon.exists():
            self.refresh_btn.setIcon(QIcon(str(ref_icon)))
            self.refresh_btn.setIconSize(QSize(16, 16))
        self.refresh_btn.clicked.connect(self._on_refresh_clicked)
        header.addWidget(self.refresh_btn)

        self.new_install_btn = OreButton("New Installation", variant="accent")
        new_icon = ORE_ICONS / "new.png"
        if new_icon.exists():
            self.new_install_btn.setIcon(QIcon(str(new_icon)))
            self.new_install_btn.setIconSize(QSize(16, 16))
        self.new_install_btn.clicked.connect(self._show_install_dialog)
        header.addWidget(self.new_install_btn)

        main_layout.addLayout(header)

        # Update Banner (shown when newer release is available)
        self.update_banner = UpdateBanner(self)
        self.update_banner.update_requested.connect(self._start_easy_update)
        main_layout.addWidget(self.update_banner)

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

    def _on_refresh_clicked(self):
        self.populate_builds()
        self.update_banner.check_updates_async(refresh=True)

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
                    self.version_activated.emit(target_version)
                    break
            self.populate_builds()
            self.update_banner.hide()
            QMessageBox.information(
                self,
                "Update Complete",
                f"Successfully updated to Minecraft Bedrock v{target_version}!\n\nYour worlds, player data, and settings remain untouched."
            )

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
        folder_icon = ORE_ICONS / "viewfolder.png"
        if folder_icon.exists():
            folder_btn.setIcon(QIcon(str(folder_icon)))
            folder_btn.setIconSize(QSize(16, 16))
        folder_btn.clicked.connect(lambda _, p=build.get("path"): self._open_folder(p))
        layout.addWidget(folder_btn)

        del_btn = OreButton("Delete", variant="warning")
        del_icon = ORE_ICONS / "delete.png"
        if del_icon.exists():
            del_btn.setIcon(QIcon(str(del_icon)))
            del_btn.setIconSize(QSize(16, 16))
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
        dlg.setFixedWidth(460)
        
        dlg_layout = QVBoxLayout(dlg)
        dlg_layout.setContentsMargins(20, 20, 20, 20)
        dlg_layout.setSpacing(12)

        # Edition Selection
        ed_box = QHBoxLayout()
        ed_lbl = QLabel("Edition:")
        ed_lbl.setStyleSheet("font-weight: bold;")
        ed_box.addWidget(ed_lbl)
        
        edition_combo = QComboBox()
        edition_combo.addItems(["release", "preview"])
        ed_box.addWidget(edition_combo, 1)
        dlg_layout.addLayout(ed_box)

        # Search / Filter Bar + Refresh Catalogue Button
        filter_box = QHBoxLayout()
        search_input = QLineEdit()
        search_input.setPlaceholderText("Filter versions…")
        filter_box.addWidget(search_input, 1)

        refresh_cat_btn = OreButton("")
        refresh_icon = ORE_ICONS / "refresh.png"
        if refresh_icon.exists():
            refresh_cat_btn.setIcon(QIcon(str(refresh_icon)))
            refresh_cat_btn.setIconSize(QSize(16, 16))
        else:
            refresh_cat_btn.setText("↻")
        refresh_cat_btn.setToolTip("Refresh version catalogue from Microsoft (bypasses 12-hour cache)")
        refresh_cat_btn.setFixedSize(36, 32)
        filter_box.addWidget(refresh_cat_btn)
        dlg_layout.addLayout(filter_box)

        # Version List Widget
        version_list = QListWidget()
        version_list.setFixedHeight(180)
        version_list.setStyleSheet("""
            QListWidget {
                background-color: #121314;
                border: 2px solid #2B2C2E;
                font-family: "Mojangles", sans-serif;
                font-size: 11px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 6px 8px;
                color: #FFFFFF;
                border-bottom: 1px solid #1E2022;
            }
            QListWidget::item:selected {
                background-color: #1A3814;
                color: #70B95C;
            }
        """)
        dlg_layout.addWidget(version_list)

        status_lbl = QLabel("Loading versions…")
        status_lbl.setObjectName("MutedText")
        status_lbl.setStyleSheet("font-size: 11px; color: #8E939C;")
        dlg_layout.addWidget(status_lbl)

        force_cb = QCheckBox("Force Re-download / Rebuild")
        dlg_layout.addWidget(force_cb)

        # Bottom Button Box
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        cancel_btn = OreButton("Cancel")
        cancel_btn.clicked.connect(dlg.reject)
        btn_box.addWidget(cancel_btn)

        install_btn = OreButton("Download and Install", variant="accent")
        install_btn.setEnabled(False)
        btn_box.addWidget(install_btn)
        dlg_layout.addLayout(btn_box)

        all_entries = []

        def _populate_versions(refresh=False):
            version_list.clear()
            status_lbl.setText("Loading catalogue from Microsoft…")
            edition = edition_combo.currentText()
            
            entries = engine.get_available_versions(edition=edition, refresh=refresh)
            all_entries.clear()
            
            all_entries.append({
                "version": "latest",
                "label": "latest  (Auto-resolve newest)",
                "installed": False,
                "is_latest": False
            })
            
            for idx, b in enumerate(entries):
                ver = b["version"]
                disp = b["display"]
                tag = ""
                if b.get("installed"):
                    tag = "  [INSTALLED]"
                elif idx == 0:
                    tag = "  [LATEST]"
                label = f"{ver} ({disp}){tag}"
                all_entries.append({
                    "version": ver,
                    "label": label,
                    "installed": b.get("installed", False),
                    "is_latest": (idx == 0)
                })
            
            _apply_filter(search_input.text())
            status_lbl.setText(f"{len(entries)} versions available.")

        def _apply_filter(text):
            query = text.strip().lower()
            version_list.clear()
            for item in all_entries:
                if not query or query in item["label"].lower() or query in item["version"].lower():
                    list_item = QListWidgetItem(item["label"])
                    list_item.setData(Qt.UserRole, item["version"])
                    if item.get("installed"):
                        list_item.setForeground(QColor("#70B95C"))
                    elif item.get("is_latest"):
                        list_item.setForeground(QColor("#55FF55"))
                    version_list.addItem(list_item)
            
            if version_list.count() > 0:
                version_list.setCurrentRow(0)
                install_btn.setEnabled(True)
            else:
                install_btn.setEnabled(False)

        def _on_start():
            selected = version_list.selectedItems()
            if not selected:
                return
            target_version = selected[0].data(Qt.UserRole)
            edition = edition_combo.currentText()
            force = force_cb.isChecked()
            
            dlg.accept()
            
            dl_dlg = DownloadDialog(edition, target_version, force=force, parent=self)
            if dl_dlg.exec():
                self.populate_builds()

        search_input.textChanged.connect(_apply_filter)
        edition_combo.currentIndexChanged.connect(lambda: _populate_versions(refresh=False))
        refresh_cat_btn.clicked.connect(lambda: _populate_versions(refresh=True))
        version_list.itemSelectionChanged.connect(lambda: install_btn.setEnabled(bool(version_list.selectedItems())))
        version_list.itemDoubleClicked.connect(lambda: _on_start())
        install_btn.clicked.connect(_on_start)

        _populate_versions(refresh=False)
        dlg.exec()
