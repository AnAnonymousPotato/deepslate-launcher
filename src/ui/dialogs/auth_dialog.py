"""
deepslate.ui.dialogs.auth_dialog
Microsoft Account device-code authentication dialog.
"""

import subprocess
import webbrowser
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QApplication, QFrame
)
from PySide6.QtCore import Qt, Signal, QObject, QSize
from PySide6.QtGui import QCursor, QIcon

from bol.auth import NativeAuth
from src.ui.theme import ORE_UI_DIR
from ..widgets.ore_button import OreButton

class AuthSignals(QObject):
    code_received = Signal(str, str) # url, code
    completed = Signal()
    error = Signal(str)


class AuthDialog(QDialog):
    """Device-code login dialog for Microsoft / Xbox accounts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sign in to Microsoft Account")
        self.setFixedWidth(440)

        self.signals = AuthSignals()
        self.signals.code_received.connect(self._on_code_received)
        self.signals.completed.connect(self._on_completed)

        self.na = NativeAuth()
        self.url = ""
        self.code = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("SIGN IN TO XBOX")
        title.setObjectName("PageTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.instruction_label = QLabel("Requesting authorization code from Microsoft...")
        self.instruction_label.setWordWrap(True)
        self.instruction_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.instruction_label)

        # Code Display Card
        self.code_card = QFrame()
        self.code_card.setObjectName("Card")
        code_card_layout = QVBoxLayout(self.code_card)
        code_card_layout.setContentsMargins(12, 12, 12, 12)
        code_card_layout.setAlignment(Qt.AlignCenter)

        self.code_label = QLabel("...")
        self.code_label.setStyleSheet(
            "font-family: monospace; font-size: 26px; font-weight: bold; color: #2ECC71; letter-spacing: 4px;"
        )
        self.code_label.setAlignment(Qt.AlignCenter)
        code_card_layout.addWidget(self.code_label)

        layout.addWidget(self.code_card)

        # Action buttons
        btn_box = QHBoxLayout()
        self.copy_btn = OreButton("Copy Code")
        self.copy_btn.clicked.connect(self._copy_code)
        self.copy_btn.setEnabled(False)
        btn_box.addWidget(self.copy_btn)

        self.open_btn = OreButton("Open Browser", variant="accent")
        self.open_btn.clicked.connect(self._open_browser)
        self.open_btn.setEnabled(False)
        btn_box.addWidget(self.open_btn)

        layout.addLayout(btn_box)

        # Cancel / Close
        cancel_box = QHBoxLayout()
        cancel_box.addStretch()
        self.close_btn = OreButton("Cancel")
        self.close_btn.clicked.connect(self._cancel)
        cancel_box.addWidget(self.close_btn)
        layout.addLayout(cancel_box)

        self.start_login()

    def start_login(self):
        def _on_auth(url, code):
            self.signals.code_received.emit(url, code)

        def _on_online():
            self.signals.completed.emit()

        self.na.start(on_auth=_on_auth, on_online=_on_online)

    def _on_code_received(self, url: str, code: str):
        self.url = url
        self.code = code
        self.code_label.setText(code)
        self.instruction_label.setText(
            f"1. Copy the code below.\n2. Open {url} in your browser and paste the code."
        )
        self.copy_btn.setEnabled(True)
        self.open_btn.setEnabled(True)
        # Automatically open the browser for convenience
        webbrowser.open(url)

    def _copy_code(self):
        if self.code:
            QApplication.clipboard().setText(self.code)
            check_icon = ORE_UI_DIR / "checkbox-checked-emerald.svg"
            if check_icon.exists():
                self.copy_btn.setIcon(QIcon(str(check_icon)))
                self.copy_btn.setIconSize(QSize(16, 16))
            self.copy_btn.setText("Copied!")

    def _open_browser(self):
        if self.url:
            webbrowser.open(self.url)

    def _on_completed(self):
        self.instruction_label.setText("Successfully signed in to Xbox Live!")
        self.instruction_label.setStyleSheet("color: #2ECC71; font-weight: bold;")
        self.code_label.setText("READY")
        self.close_btn.setText("Close")
        self.accept()

    def _cancel(self):
        self.na._stop = True
        self.reject()
