"""
deepslate.ui.widgets.sidebar
Modern Minecraft Launcher styled navigation sidebar.
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QSpacerItem, QSizePolicy, QMenu
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QIcon, QCursor, QAction

from src.bridge.engine import engine
from src.ui.theme import ICONS_DIR

class Sidebar(QFrame):
    """Left navigation sidebar matching the Minecraft Launcher layout."""
    
    page_changed = Signal(str)
    auth_requested = Signal()
    store_link_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(230)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(6)
        
        # 1. Branding Header
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(4, 4, 4, 12)
        header_layout.setSpacing(10)
        
        bedrock_icon_path = ICONS_DIR / "bedrock.png"
        icon_label = QLabel()
        if bedrock_icon_path.exists():
            pix = QPixmap(str(bedrock_icon_path)).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pix)
        
        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        title_label = QLabel("DEEPSLATE")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF; letter-spacing: 1px;")
        sub_label = QLabel("Bedrock Edition")
        sub_label.setStyleSheet("font-size: 10px; color: #2ECC71; font-weight: bold;")
        title_box.addWidget(title_label)
        title_box.addWidget(sub_label)
        
        header_layout.addWidget(icon_label)
        header_layout.addLayout(title_box)
        header_layout.addStretch()
        layout.addWidget(header_widget)

        # Divider
        divider = QFrame()
        divider.setStyleSheet("background-color: #2B2C2E; max-height: 1px;")
        layout.addWidget(divider)
        layout.addSpacing(6)

        # 2. Nav Items
        self.buttons: dict[str, QPushButton] = {}
        nav_items = [
            ("play", "🎮  Play"),
            ("installations", "📦  Installations"),
            ("settings", "⚙️  Settings"),
            ("tools", "🛠️  Tools && Diag"),
            ("profiles", "👤  Profiles"),
            ("changelog", "📜  Patch Notes"),
        ]
        
        for key, label in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("SidebarNavButton")
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.clicked.connect(lambda checked=False, k=key: self.set_active_page(k))
            self.buttons[key] = btn
            layout.addWidget(btn)

        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # 3. Bottom Account Card
        self.account_card = QFrame()
        self.account_card.setObjectName("Card")
        self.account_card.setStyleSheet(
            "QFrame#Card { background-color: #202122; border: 2px solid #303133; padding: 6px 8px; }"
            "QFrame#Card:hover { border: 2px solid #4B9736; }"
        )
        self.account_card.setCursor(QCursor(Qt.PointingHandCursor))
        self.account_card.mousePressEvent = self._show_account_menu

        acct_layout = QHBoxLayout(self.account_card)
        acct_layout.setContentsMargins(6, 6, 6, 6)
        acct_layout.setSpacing(8)

        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("color: #2ECC71; font-size: 12px;")

        self.gamertag_label = QLabel("Not Signed In")
        self.gamertag_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #FFFFFF;")

        acct_layout.addWidget(self.status_dot)
        acct_layout.addWidget(self.gamertag_label, 1)

        menu_hint = QLabel("▾")
        menu_hint.setStyleSheet("color: #88898C; font-size: 10px;")
        acct_layout.addWidget(menu_hint)

        layout.addWidget(self.account_card)

        # Default active page
        self.set_active_page("play")
        self.refresh_account_display()

    def set_active_page(self, page_key: str):
        for k, btn in self.buttons.items():
            is_active = (k == page_key)
            btn.setProperty("active", "true" if is_active else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.page_changed.emit(page_key)

    def refresh_account_display(self):
        signed_in = engine.is_signed_in()
        if signed_in:
            gt = engine.get_account_gamertag() or "Xbox Player"
            self.gamertag_label.setText(gt)
            self.status_dot.setStyleSheet("color: #2ECC71; font-size: 12px;")
        else:
            self.gamertag_label.setText("Sign In (Xbox)")
            self.status_dot.setStyleSheet("color: #C0392B; font-size: 12px;")

    def _show_account_menu(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background-color: #222324; border: 2px solid #4B9736; padding: 4px; }"
            "QMenu::item { padding: 6px 20px; color: #FFFFFF; font-family: Mojangles; }"
            "QMenu::item:selected { background-color: #4B9736; }"
        )

        signed_in = engine.is_signed_in()
        store_linked = engine.is_store_account_linked()

        if signed_in:
            gt = engine.get_account_gamertag() or "Unknown"
            info_act = QAction(f"Signed in as: {gt}", self)
            info_act.setEnabled(False)
            menu.addAction(info_act)
            menu.addSeparator()

            store_text = "✓ Store Account Linked" if store_linked else "Link Microsoft Store Account"
            store_act = menu.addAction(store_text)
            store_act.triggered.connect(self.store_link_requested.emit)

            sign_out_act = menu.addAction("Sign Out")
            sign_out_act.triggered.connect(self._handle_sign_out)
        else:
            sign_in_act = menu.addAction("Sign In with Microsoft Account")
            sign_in_act.triggered.connect(self.auth_requested.emit)

            store_act = menu.addAction("Link Microsoft Store Account")
            store_act.triggered.connect(self.store_link_requested.emit)

        menu.exec(self.account_card.mapToGlobal(event.pos()))

    def _handle_sign_out(self):
        engine.sign_out()
        self.refresh_account_display()
