"""
deepslate.ui.pages.profiles_page
Xbox profiles manager page.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QInputDialog, QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt, Signal

from src.bridge.engine import engine
from ..widgets.ore_button import OreButton

class ProfilesPage(QWidget):
    """Isolated Xbox profiles manager."""

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("XBOX PROFILES")
        title.setObjectName("PageTitle")
        header.addWidget(title)
        header.addStretch()

        create_btn = OreButton("+ Create Profile", variant="accent")
        create_btn.clicked.connect(self._create_profile)
        header.addWidget(create_btn)

        main_layout.addLayout(header)

        desc = QLabel("Isolated profiles have their own Microsoft/Xbox login, worlds, and settings.")
        desc.setObjectName("MutedText")
        main_layout.addWidget(desc)

        # Scroll area for profile list
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(10)
        self.container_layout.addStretch()

        self.scroll.setWidget(self.container)
        main_layout.addWidget(self.scroll)

        self.refresh_profiles()

    def refresh_profiles(self):
        while self.container_layout.count() > 1:
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        profiles = engine.get_profiles()
        current = engine.get_current_profile()

        # Always list Default if not present
        if "Default" not in profiles:
            profiles = ["Default"] + profiles

        for p in profiles:
            card = self._create_profile_card(p, p == current)
            self.container_layout.insertWidget(self.container_layout.count() - 1, card)

    def _create_profile_card(self, name: str, is_active: bool) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        info = QVBoxLayout()
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFFFFF;")
        info.addWidget(name_lbl)

        if is_active:
            status = QLabel("Active Profile")
            status.setObjectName("StatusBadge")
            info.addWidget(status)

        layout.addLayout(info, 1)

        sc_btn = OreButton("Shortcut")
        sc_btn.clicked.connect(lambda _, n=name: self._make_shortcut(n))
        layout.addWidget(sc_btn)

        if name != "Default":
            del_btn = OreButton("Delete", variant="warning")
            del_btn.clicked.connect(lambda _, n=name: self._delete_profile(n))
            layout.addWidget(del_btn)

        return card

    def _create_profile(self):
        name, ok = QInputDialog.getText(self, "Create Profile", "Enter new profile name:")
        if ok and name.strip():
            try:
                engine.create_new_profile(name.strip())
                self.refresh_profiles()
            except Exception as exc:
                QMessageBox.critical(self, "Error", str(exc))

    def _delete_profile(self, name: str):
        reply = QMessageBox.question(
            self,
            "Delete Profile",
            f"Are you sure you want to delete profile '{name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                engine.remove_profile(name)
                self.refresh_profiles()
            except Exception as exc:
                QMessageBox.critical(self, "Error", str(exc))

    def _make_shortcut(self, name: str):
        try:
            p = engine.make_desktop_shortcut(name)
            QMessageBox.information(self, "Shortcut Created", f"Shortcut created at:\n{p}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
