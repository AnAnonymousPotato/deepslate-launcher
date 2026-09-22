"""
deepslate.ui.dialogs.download_dialog
Reusable download and installation progress dialog for Minecraft Bedrock builds.
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QThread
from src.bridge.engine import engine
from src.ui.widgets.ore_button import OreButton


class DownloadWorker(QThread):
    progress = Signal(int, int)   # done, total in bytes
    finished = Signal(bool, str)  # success, message

    def __init__(self, edition: str, version: str, force: bool = False):
        super().__init__()
        self.edition = edition
        self.version = version
        self.force = force

    def run(self):
        try:
            def _cb(done, total):
                self.progress.emit(int(done or 0), int(total or 0))

            target_ver = self.version if self.version and self.version != "latest" else None
            engine.install_build(
                edition=self.edition,
                version=target_ver,
                force=self.force,
                progress_cb=_cb
            )
            self.finished.emit(True, "Installation complete.")
        except Exception as exc:
            self.finished.emit(False, str(exc))


class DownloadDialog(QDialog):
    """Modal dialog displaying download & extraction progress for a build."""

    installation_finished = Signal(bool, str)

    def __init__(self, edition: str, version: str, display_name: str = "", force: bool = False, parent=None):
        super().__init__(parent)
        self.edition = edition
        self.version = version
        self.force = force
        self.success = False

        self.setWindowTitle("Downloading Minecraft Bedrock")
        self.setFixedWidth(460)
        self.setStyleSheet("""
            QDialog {
                background-color: #18191A;
                border: 2px solid #3B8526;
            }
            QLabel {
                font-family: "Mojangles", sans-serif;
                color: #FFFFFF;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        name_str = display_name if display_name else f"Minecraft Bedrock v{version}"
        self.title_lbl = QLabel(f"Downloading {name_str}")
        self.title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #70B95C;")
        layout.addWidget(self.title_lbl)

        self.status_lbl = QLabel("Contacting Microsoft Store CDN…")
        self.status_lbl.setStyleSheet("font-size: 11px; color: #CCCCCC;")
        layout.addWidget(self.status_lbl)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        self.cancel_btn = OreButton("Cancel")
        self.cancel_btn.clicked.connect(self._cancel)
        btn_box.addWidget(self.cancel_btn)
        layout.addLayout(btn_box)

        # Start worker
        self.worker = DownloadWorker(self.edition, self.version, self.force)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, done: int, total: int):
        if total > 0:
            self.progress_bar.setRange(0, 100)
            pct = int((done / total) * 100)
            self.progress_bar.setValue(pct)
            done_mb = done / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            self.status_lbl.setText(f"Downloading: {pct}% ({done_mb:.1f} / {total_mb:.1f} MB)")
        else:
            self.progress_bar.setRange(0, 0)
            self.status_lbl.setText("Extracting & verifying package integrity…")

    def _on_finished(self, success: bool, message: str):
        self.success = success
        if success:
            self.status_lbl.setText("Installation completed successfully!")
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            self.cancel_btn.setText("Close")
            self.installation_finished.emit(True, self.version)
            self.accept()
        else:
            self.status_lbl.setText(f"Failed: {message}")
            QMessageBox.critical(self, "Installation Failed", f"Could not install Minecraft build:\n\n{message}")
            self.installation_finished.emit(False, message)
            self.reject()

    def _cancel(self):
        if self.worker.isRunning():
            self.worker.terminate()
        self.reject()
