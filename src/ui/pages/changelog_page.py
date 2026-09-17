"""
deepslate.ui.pages.changelog_page
Patch notes and changelog viewer page.
"""

from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextBrowser
from PySide6.QtCore import Qt

from src.bridge.cli_bridge import run_cli_command

class ChangelogPage(QWidget):
    """Markdown / rich text viewer for release notes."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)

        title = QLabel("PATCH NOTES & CHANGELOG")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        self.browser = QTextBrowser()
        self.browser.setObjectName("ChangelogBrowser")
        self.browser.setOpenExternalLinks(True)
        layout.addWidget(self.browser, 1)

        self.load_changelog()

    def load_changelog(self):
        # Try reading changelog from CLI or local file
        code, out, _ = run_cli_command(["changelog"])
        if code == 0 and out.strip():
            self.browser.setMarkdown(out)
        else:
            # Fallback text
            self.browser.setMarkdown(
                "# Deepslate Launcher\n\n"
                "A modern Minecraft-themed Bedrock Launcher for Linux.\n\n"
                "- Built with PySide6 & Ore UI (Dark Emerald).\n"
                "- Seamless integration with `bedrock-on-linux-bin`.\n"
                "- Update-proof architecture."
            )
