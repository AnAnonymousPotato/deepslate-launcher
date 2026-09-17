"""
deepslate.ui.theme
Ore UI (Dark Emerald) theme loader and QSS generator for Deepslate Launcher.
"""

from pathlib import Path
from PySide6.QtGui import QFontDatabase, QFont
from PySide6.QtWidgets import QApplication

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = PROJECT_ROOT / "assets"
ORE_UI_DIR = ASSETS_DIR / "ore_ui"
FONTS_DIR = ASSETS_DIR / "fonts"
ICONS_DIR = ASSETS_DIR / "icons"
IMAGES_DIR = ASSETS_DIR / "images"

def init_fonts():
    """Register Mojangles and Minecraftia fonts with Qt."""
    for font_file in FONTS_DIR.glob("*.*tf"):
        QFontDatabase.addApplicationFont(str(font_file))

def get_font(size: int = 12, bold: bool = False) -> QFont:
    """Return Mojangles font if available, fallback to sans-serif."""
    families = QFontDatabase.families()
    family = "Mojangles" if "Mojangles" in families else "sans-serif"
    font = QFont(family, size)
    if bold:
        font.setBold(True)
    return font

def get_pixel_font(size: int = 10) -> QFont:
    """Return Minecraftia font if available."""
    families = QFontDatabase.families()
    family = "Minecraftia" if "Minecraftia" in families else "monospace"
    return QFont(family, size)

def generate_qss() -> str:
    """Generate the full Ore UI Dark Emerald QSS stylesheet."""
    ui_path = str(ORE_UI_DIR).replace("\\", "/")
    
    return f"""
    /* =========================================================================
       Deepslate Launcher — Ore UI (Dark Emerald) Stylesheet
       ========================================================================= */
    
    * {{
        font-family: "Mojangles", "Noto Sans", sans-serif;
        color: #E0E0E0;
    }}

    QMainWindow, #RootWindow, #CentralWidget {{
        background-color: #161718;
        border: none;
    }}

    QWidget {{
        background-color: transparent;
        selection-background-color: #4B9736;
        selection-color: #FFFFFF;
    }}

    /* --- ScrollBars --- */
    QScrollBar:vertical {{
        background: #1C1D1D;
        width: 14px;
        margin: 0px;
        border-left: 2px solid #2A2B2C;
    }}
    QScrollBar::handle:vertical {{
        background: #39393B;
        min-height: 24px;
        border: 2px solid #2A2B2C;
        margin: 2px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: #47484A;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar:horizontal {{
        background: #1C1D1D;
        height: 14px;
        margin: 0px;
        border-top: 2px solid #2A2B2C;
    }}
    QScrollBar::handle:horizontal {{
        background: #39393B;
        min-width: 24px;
        border: 2px solid #2A2B2C;
        margin: 2px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: #47484A;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* --- Ore UI Buttons --- */
    QPushButton, QToolButton {{
        font-family: "Mojangles", sans-serif;
        font-size: 13px;
        color: #FFFFFF;
        background-color: #39393B;
        border: 4px;
        border-bottom: 8px;
        border-image: url("{ui_path}/button-default-default.svg") 4 4 8 4 repeat;
        min-height: 26px;
        padding-left: 14px;
        padding-right: 14px;
        padding-top: 2px;
        padding-bottom: 4px;
        outline: none;
    }}

    QPushButton:hover, QToolButton:hover {{
        background-color: #47484A;
        border-image: url("{ui_path}/button-default-hover.svg") 4 4 8 4 repeat;
    }}

    QPushButton:pressed, QToolButton:pressed {{
        background-color: #2A2B2C;
        border-bottom: 4px;
        border-image: url("{ui_path}/checkbox-disabled.svg") 4 4 4 4 repeat;
        margin-top: 4px;
    }}

    QPushButton:disabled, QToolButton:disabled {{
        color: #737476;
        background-color: #2A2B2C;
        border-image: url("{ui_path}/button-default-default.svg") 4 4 8 4 repeat;
    }}

    /* Primary / Play Emerald Accent Button */
    QPushButton#PlayButton, QPushButton#AccentButton {{
        font-size: 15px;
        font-weight: bold;
        color: #FFFFFF;
        background-color: #4B9736;
        border: 4px;
        border-bottom: 8px;
        border-image: url("{ui_path}/button-accent-default.svg") 4 4 8 4 repeat;
        min-height: 34px;
        padding-left: 20px;
        padding-right: 20px;
    }}

    QPushButton#PlayButton:hover, QPushButton#AccentButton:hover {{
        border-image: url("{ui_path}/button-accent-hover.svg") 4 4 8 4 repeat;
    }}

    QPushButton#PlayButton:pressed, QPushButton#AccentButton:pressed {{
        border-bottom: 4px;
        border-image: url("{ui_path}/button-accent-pressed-menu.svg") 4 4 4 4 repeat;
        margin-top: 4px;
    }}

    /* Warning / Kill Button */
    QPushButton#KillButton, QPushButton#WarningButton {{
        font-size: 14px;
        font-weight: bold;
        color: #FFFFFF;
        background-color: #C0392B;
        border: 4px;
        border-bottom: 8px;
        border-image: url("{ui_path}/button-warning-default.svg") 4 4 8 4 repeat;
        min-height: 30px;
        padding-left: 16px;
        padding-right: 16px;
    }}

    QPushButton#KillButton:hover, QPushButton#WarningButton:hover {{
        border-image: url("{ui_path}/button-warning-hover.svg") 4 4 8 4 repeat;
    }}

    QPushButton#KillButton:pressed, QPushButton#WarningButton:pressed {{
        border-bottom: 4px;
        border-image: url("{ui_path}/button-warning-pressed.svg") 4 4 4 4 repeat;
        margin-top: 4px;
    }}

    /* --- Sidebar Nav Buttons --- */
    QPushButton#SidebarNavButton {{
        text-align: left;
        font-size: 13px;
        padding-left: 16px;
        min-height: 38px;
        background: transparent;
        border: 2px solid transparent;
        border-radius: 0px;
        border-image: none;
    }}
    QPushButton#SidebarNavButton:hover {{
        background-color: #262729;
        border-left: 4px solid #4B9736;
    }}
    QPushButton#SidebarNavButton[active="true"] {{
        background-color: #2A2B2C;
        border-left: 4px solid #2ECC71;
        color: #2ECC71;
        font-weight: bold;
    }}

    /* --- Inputs & Comboboxes --- */
    QLineEdit, QSpinBox, QComboBox {{
        background-color: #222324;
        border: 2px solid #39393B;
        color: #FFFFFF;
        padding: 6px 10px;
        font-size: 13px;
        min-height: 24px;
    }}
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
        border: 2px solid #4B9736;
        background-color: #1C1D1D;
    }}

    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 24px;
        border-left: 2px solid #39393B;
    }}
    QComboBox::down-arrow {{
        image: url("{ui_path}/combobox-arrow.svg");
        width: 12px;
        height: 12px;
    }}
    QComboBox QAbstractItemView {{
        background-color: #222324;
        border: 2px solid #4B9736;
        color: #FFFFFF;
        selection-background-color: #4B9736;
        selection-color: #FFFFFF;
        padding: 4px;
    }}

    /* --- Checkboxes --- */
    QCheckBox {{
        spacing: 8px;
        font-size: 13px;
        color: #E0E0E0;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
    }}
    QCheckBox::indicator:unchecked {{
        image: url("{ui_path}/checkbox-unchecked-default.svg");
    }}
    QCheckBox::indicator:unchecked:hover {{
        image: url("{ui_path}/checkbox-unchecked-hover.svg");
    }}
    QCheckBox::indicator:checked {{
        image: url("{ui_path}/checkbox-checked-default.svg");
    }}
    QCheckBox::indicator:checked:hover {{
        image: url("{ui_path}/checkbox-checked-hover.svg");
    }}

    /* --- Frames & Cards --- */
    QFrame#Card, QFrame#Panel {{
        background-color: #222324;
        border: 2px solid #303133;
        padding: 12px;
    }}
    QFrame#HeaderCard {{
        background-color: #1F2021;
        border-bottom: 2px solid #303133;
    }}
    QFrame#Sidebar {{
        background-color: #191A1B;
        border-right: 2px solid #2B2C2E;
    }}

    /* --- Text Elements --- */
    QLabel#PageTitle {{
        font-size: 20px;
        font-weight: bold;
        color: #FFFFFF;
    }}
    QLabel#SectionHeader {{
        font-size: 15px;
        font-weight: bold;
        color: #2ECC71;
        margin-top: 8px;
        margin-bottom: 4px;
    }}
    QLabel#MutedText {{
        color: #88898C;
        font-size: 11px;
    }}
    QLabel#StatusBadge {{
        color: #2ECC71;
        background-color: #123D06;
        border: 1px solid #4B9736;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: bold;
    }}

    /* --- Progress Bar --- */
    QProgressBar {{
        background-color: #1C1D1D;
        border: 2px solid #39393B;
        text-align: center;
        color: #FFFFFF;
        font-weight: bold;
        height: 18px;
    }}
    QProgressBar::chunk {{
        background-color: #4B9736;
    }}

    /* --- Real-Time Console / Log Drawer --- */
    QPlainTextEdit#ConsoleDrawer, QTextBrowser#ChangelogBrowser {{
        background-color: #121314;
        border: 2px solid #2B2C2E;
        color: #7FE0A0;
        font-family: "Minecraftia", monospace;
        font-size: 11px;
        padding: 8px;
    }}

    /* --- Tab Widget --- */
    QTabWidget::pane {{
        border: 2px solid #303133;
        background-color: #222324;
        top: -2px;
    }}
    QTabBar::tab {{
        background-color: #191A1B;
        color: #A0A0A0;
        border: 2px solid #303133;
        border-bottom: none;
        padding: 8px 16px;
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        background-color: #222324;
        color: #2ECC71;
        border-top: 3px solid #2ECC71;
        font-weight: bold;
    }}
    QTabBar::tab:hover:!selected {{
        background-color: #242526;
        color: #FFFFFF;
    }}
    """
