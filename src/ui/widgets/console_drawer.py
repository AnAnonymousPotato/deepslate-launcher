"""
deepslate.ui.widgets.console_drawer
Collapsible live log console drawer.
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QApplication
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor

class ConsoleDrawer(QFrame):
    """Collapsible bottom log console for Wine, Proton, and launcher output."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.is_expanded = False
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 6, 8, 6)
        self.main_layout.setSpacing(6)
        
        # Header bar
        header = QHBoxLayout()
        header.setSpacing(8)
        
        self.toggle_btn = QPushButton("▶ Show Logs / Console")
        self.toggle_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.toggle_btn.clicked.connect(self.toggle)
        self.toggle_btn.setStyleSheet("font-size: 11px; padding: 4px 8px; min-height: 20px;")
        
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("MutedText")
        
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.copy_btn.clicked.connect(self.copy_logs)
        self.copy_btn.setStyleSheet("font-size: 11px; padding: 4px 8px; min-height: 20px;")
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.clear_btn.clicked.connect(self.clear_logs)
        self.clear_btn.setStyleSheet("font-size: 11px; padding: 4px 8px; min-height: 20px;")

        header.addWidget(self.toggle_btn)
        header.addWidget(self.status_label, 1)
        header.addWidget(self.copy_btn)
        header.addWidget(self.clear_btn)
        
        self.main_layout.addLayout(header)
        
        # Text view
        self.text_edit = QPlainTextEdit()
        self.text_edit.setObjectName("ConsoleDrawer")
        self.text_edit.setReadOnly(True)
        self.text_edit.setMaximumBlockCount(2000)
        self.text_edit.setFixedHeight(140)
        self.text_edit.hide()
        
        self.main_layout.addWidget(self.text_edit)

    def toggle(self):
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.text_edit.show()
            self.toggle_btn.setText("▼ Hide Logs / Console")
        else:
            self.text_edit.hide()
            self.toggle_btn.setText("▶ Show Logs / Console")

    def append_log(self, text: str):
        self.text_edit.appendPlainText(text.rstrip())
        self.text_edit.verticalScrollBar().setValue(
            self.text_edit.verticalScrollBar().maximum()
        )

    def copy_logs(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())

    def clear_logs(self):
        self.text_edit.clear()

    def set_status(self, text: str):
        self.status_label.setText(text)
