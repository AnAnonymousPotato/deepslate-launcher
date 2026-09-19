"""
deepslate.ui.pages.changelog_page
Patch notes and changelog viewer page with dark theme formatting.
"""

import re
import html
from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextBrowser, QHBoxLayout
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

from src.bridge.cli_bridge import run_cli_command
from src.ui.widgets.ore_button import OreButton

def format_markdown_to_html(md_text: str) -> str:
    """Format raw markdown into dark-themed Minecraft styled HTML."""
    try:
        import markdown
        body_html = markdown.markdown(md_text)
    except ImportError:
        body_html = f"<pre>{html.escape(md_text)}</pre>"

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body {{
        color: #D6D7D8;
        background-color: #121314;
        font-family: -apple-system, "Segoe UI", "Noto Sans", sans-serif;
        font-size: 13px;
        line-height: 1.6;
        margin: 16px 20px;
    }}
    h1, h2 {{
        color: #55FF55;
        font-family: "Mojangles", sans-serif;
        font-size: 17px;
        border-bottom: 2px solid #2B2C2E;
        padding-bottom: 6px;
        margin-top: 24px;
        margin-bottom: 12px;
    }}
    h3, h4 {{
        color: #7FE0A0;
        font-family: "Mojangles", sans-serif;
        font-size: 13px;
        margin-top: 14px;
        margin-bottom: 6px;
    }}
    ul {{
        margin-left: 18px;
        padding-left: 0px;
    }}
    li {{
        margin-bottom: 8px;
        color: #D6D7D8;
    }}
    p {{
        margin: 6px 0;
        color: #D6D7D8;
    }}
    a {{
        color: #5294E2;
        text-decoration: underline;
    }}
    code {{
        background-color: #222324;
        color: #55FF55;
        font-family: monospace;
        padding: 2px 5px;
        border-radius: 3px;
    }}
    strong {{
        color: #FFFFFF;
    }}
    em {{
        color: #A0C080;
    }}
</style>
</head>
<body>
{body_html}
</body>
</html>"""


class ChangelogPage(QWidget):
    """Patch notes and changelog viewer page."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("PATCH NOTES")
        title.setObjectName("PageTitle")
        header.addWidget(title)
        header.addStretch()

        refresh_btn = OreButton("Refresh Notes")
        refresh_btn.clicked.connect(self.load_changelog)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        self.browser = QTextBrowser()
        self.browser.setObjectName("ChangelogBrowser")
        self.browser.setOpenExternalLinks(True)

        # Set palette so text is always bright white/light grey
        pal = self.browser.palette()
        pal.setColor(QPalette.Text, QColor("#E0E0E0"))
        pal.setColor(QPalette.WindowText, QColor("#E0E0E0"))
        pal.setColor(QPalette.Base, QColor("#121314"))
        self.browser.setPalette(pal)

        layout.addWidget(self.browser, 1)

        self.load_changelog()

    def load_changelog(self):
        code, out, _ = run_cli_command(["changelog"])
        if code == 0 and out.strip():
            formatted = format_markdown_to_html(out)
            self.browser.setHtml(formatted)
        else:
            fallback = (
                "# Deepslate Launcher v1.0.0\n\n"
                "### Modern Minecraft Bedrock Experience on Linux\n\n"
                "- Built with PySide6 & Ore UI (Dark Emerald).\n"
                "- High-resolution 9-slice vector assets.\n"
                "- Live process streaming and automatic AUR update compatibility."
            )
            self.browser.setHtml(format_markdown_to_html(fallback))
