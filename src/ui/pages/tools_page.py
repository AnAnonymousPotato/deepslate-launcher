"""
deepslate.ui.pages.tools_page
Tools, diagnostics, and prefix repair page.
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPlainTextEdit, QFileDialog, QMessageBox, QTabWidget
)
from PySide6.QtCore import Qt, QThread, Signal

from src.bridge.engine import engine
from ..widgets.ore_button import OreButton

class CommandWorker(QThread):
    output_ready = Signal(str)
    finished = Signal(int)

    def __init__(self, task_fn):
        super().__init__()
        self.task_fn = task_fn

    def run(self):
        code, text = self.task_fn()
        self.output_ready.emit(text)
        self.finished.emit(code)


class ToolsPage(QWidget):
    """System diagnostics, prefix repair, shortcuts, and content import."""

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(12)

        title = QLabel("TOOLS & DIAGNOSTICS")
        title.setObjectName("PageTitle")
        main_layout.addWidget(title)

        # Tabs: Doctor & Network | Maintenance & Import
        tabs = QTabWidget()
        tabs.addTab(self._build_diag_tab(), "Diagnostics")
        tabs.addTab(self._build_maintenance_tab(), "Maintenance && Import")
        main_layout.addWidget(tabs)

    def _build_diag_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        btn_row = QHBoxLayout()
        doctor_btn = OreButton("Run System Doctor")
        doctor_btn.clicked.connect(self._run_doctor)
        btn_row.addWidget(doctor_btn)

        net_btn = OreButton("Run Network Diagnostics")
        net_btn.clicked.connect(self._run_network)
        btn_row.addWidget(net_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.diag_console = QPlainTextEdit()
        self.diag_console.setObjectName("ConsoleDrawer")
        self.diag_console.setReadOnly(True)
        layout.addWidget(self.diag_console, 1)

        return w

    def _build_maintenance_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # 1. Content Import
        c_hdr = QLabel("Import Content")
        c_hdr.setObjectName("SectionHeader")
        layout.addWidget(c_hdr)

        import_desc = QLabel("Import .mcpack, .mcaddon, .mcworld, .mctemplate, or .mcskin directly into Minecraft.")
        import_desc.setObjectName("MutedText")
        layout.addWidget(import_desc)

        import_btn = OreButton("Select File(s) to Import...")
        import_btn.clicked.connect(self._import_files)
        layout.addWidget(import_btn)

        # 2. Desktop Shortcut
        s_hdr = QLabel("Desktop & Steam Shortcut")
        s_hdr.setObjectName("SectionHeader")
        layout.addWidget(s_hdr)

        sc_desc = QLabel("Create a direct launcher shortcut on your Desktop / application menu.")
        sc_desc.setObjectName("MutedText")
        layout.addWidget(sc_desc)

        sc_btn = OreButton("Create Direct Play Shortcut")
        sc_btn.clicked.connect(self._make_shortcut)
        layout.addWidget(sc_btn)

        # 3. Wine Prefix Repair
        r_hdr = QLabel("Repair Wine Prefix")
        r_hdr.setObjectName("SectionHeader")
        layout.addWidget(r_hdr)

        rep_desc = QLabel("Recreates the Wine prefix and reinstalls GameInput and dependencies. (Game files and worlds are preserved).")
        rep_desc.setObjectName("MutedText")
        layout.addWidget(rep_desc)

        rep_btn = OreButton("Reset Wine Prefix", variant="warning")
        rep_btn.clicked.connect(self._repair_prefix)
        layout.addWidget(rep_btn)

        layout.addStretch()
        return w

    def _run_doctor(self):
        self.diag_console.clear()
        self.diag_console.appendPlainText("Running System Doctor...")
        self.worker = CommandWorker(engine.run_system_doctor)
        self.worker.output_ready.connect(self.diag_console.appendPlainText)
        self.worker.start()

    def _run_network(self):
        self.diag_console.clear()
        self.diag_console.appendPlainText("Running Network Diagnostics...")
        self.worker = CommandWorker(engine.run_network_doctor)
        self.worker.output_ready.connect(self.diag_console.appendPlainText)
        self.worker.start()

    def _import_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Content to Import",
            str(Path.home()),
            "Minecraft Content (*.mcpack *.mcaddon *.mcworld *.mctemplate *.mcskin);;All Files (*)"
        )
        if files:
            try:
                count, paths = engine.import_game_content(files)
                QMessageBox.information(self, "Import Successful", f"Successfully imported {count} file(s).")
            except Exception as exc:
                QMessageBox.critical(self, "Import Failed", str(exc))

    def _make_shortcut(self):
        try:
            path = engine.make_desktop_shortcut()
            QMessageBox.information(self, "Shortcut Created", f"Desktop shortcut created at:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def _repair_prefix(self):
        reply = QMessageBox.question(
            self,
            "Reset Prefix",
            "Are you sure you want to reset the Wine prefix?\nYour worlds and settings will not be lost.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                engine.reset_wine_prefix()
                QMessageBox.information(self, "Reset Complete", "Wine prefix reset successfully.")
            except Exception as exc:
                QMessageBox.critical(self, "Error", str(exc))
