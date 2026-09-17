"""
deepslate.ui.main_window
Main application window combining sidebar navigation, pages, and console drawer.
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap

from .theme import generate_qss, init_fonts
from .widgets.sidebar import Sidebar
from .widgets.console_drawer import ConsoleDrawer
from .pages.play_page import PlayPage
from .pages.installations_page import InstallationsPage
from .pages.settings_page import SettingsPage
from .pages.tools_page import ToolsPage
from .pages.profiles_page import ProfilesPage
from .pages.changelog_page import ChangelogPage
from .dialogs.auth_dialog import AuthDialog
from src.bridge.engine import engine

ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets"
ICONS_DIR = ASSETS_DIR / "icons"

class MainWindow(QMainWindow):
    """Deepslate Launcher Main Window."""

    def __init__(self):
        super().__init__()
        self.setObjectName("RootWindow")
        self.setWindowTitle("Deepslate Launcher — Minecraft Bedrock")
        self.resize(1080, 700)
        self.setMinimumSize(920, 600)

        # Set Icon
        icon_path = ICONS_DIR / "app_icon.png"
        if not icon_path.exists():
            icon_path = ICONS_DIR / "bedrock.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Central Widget & Outer Layout
        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)

        outer_layout = QHBoxLayout(central)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # 1. Left Sidebar
        self.sidebar = Sidebar(self)
        self.sidebar.page_changed.connect(self._on_page_changed)
        self.sidebar.auth_requested.connect(self._show_auth_dialog)
        self.sidebar.store_link_requested.connect(self._link_store_account)
        outer_layout.addWidget(self.sidebar)

        # 2. Right Content Area (Pages + Bottom Console Drawer)
        content_wrapper = QWidget()
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Stacked Pages
        self.stack = QStackedWidget()
        self.play_page = PlayPage()
        self.installations_page = InstallationsPage()
        self.settings_page = SettingsPage()
        self.tools_page = ToolsPage()
        self.profiles_page = ProfilesPage()
        self.changelog_page = ChangelogPage()

        self.pages = {
            "play": self.play_page,
            "installations": self.installations_page,
            "settings": self.settings_page,
            "tools": self.tools_page,
            "profiles": self.profiles_page,
            "changelog": self.changelog_page,
        }

        for p in self.pages.values():
            self.stack.addWidget(p)

        content_layout.addWidget(self.stack, 1)

        # Bottom Console Drawer
        self.console_drawer = ConsoleDrawer(self)
        content_layout.addWidget(self.console_drawer)

        outer_layout.addWidget(content_wrapper, 1)

        # Wire Inter-page Signals
        self.installations_page.version_activated.connect(lambda _: self.play_page.refresh_versions())
        self.play_page.launch_requested.connect(self._start_game_launch)
        self.play_page.kill_requested.connect(self._stop_game)

        # Apply Ore UI Theme
        self.apply_theme()

    def apply_theme(self):
        init_fonts()
        qss = generate_qss()
        self.setStyleSheet(qss)

    def _on_page_changed(self, key: str):
        if key in self.pages:
            self.stack.setCurrentWidget(self.pages[key])
            if key == "play":
                self.play_page.refresh_versions()
            elif key == "installations":
                self.installations_page.populate_builds()
            elif key == "profiles":
                self.profiles_page.refresh_profiles()

    def _start_game_launch(self):
        self.console_drawer.append_log("[Deepslate] Launching Minecraft Bedrock...")
        self.console_drawer.set_status("Minecraft launching...")

        def _on_log(line: str):
            # Safe call back into UI thread
            QTimer.singleShot(0, lambda: self.console_drawer.append_log(line))

        def _on_exit(code: int):
            def _handle():
                status = "Minecraft exited normally." if code == 0 else f"Minecraft exited with code {code}."
                self.console_drawer.append_log(f"[Deepslate] {status}")
                self.console_drawer.set_status("Ready")
                self.play_page.set_game_running(False)
            QTimer.singleShot(0, _handle)

        engine.launch_game_async(log_callback=_on_log, exit_callback=_on_exit)

        if engine.get_setting("close_on_launch", False):
            self.hide()

    def _stop_game(self):
        self.console_drawer.append_log("[Deepslate] Terminating Minecraft...")
        engine.kill_game()

    def _show_auth_dialog(self):
        dlg = AuthDialog(self)
        if dlg.exec():
            self.sidebar.refresh_account_display()

    def _link_store_account(self):
        from bol import xodus
        if xodus.signed_in():
            QMessageBox.information(self, "Microsoft Store", "A Microsoft Store account is already linked.")
        else:
            try:
                xodus.login()
                QMessageBox.information(self, "Microsoft Store", "Store account linked successfully.")
                self.sidebar.refresh_account_display()
            except Exception as exc:
                QMessageBox.critical(self, "Store Login Failed", str(exc))
