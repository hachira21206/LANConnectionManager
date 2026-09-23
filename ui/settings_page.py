"""Settings page for network, appearance, logging, and database configuration."""
import logging
import os
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QSpinBox, QComboBox, QGroupBox,
    QFormLayout, QFileDialog, QScrollArea, QMessageBox
)
from PySide6.QtCore import Signal

from database.database import DatabaseManager
from database.repository import SettingsRepository

logger = logging.getLogger(__name__)


class SettingsPage(QWidget):
    """Application settings page."""

    show_toast = Signal(str, str)
    theme_changed = Signal(str)

    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self._db = db
        self._settings_repo = SettingsRepository(db)
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        """Build settings page layout."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 0, 24, 24)
        layout.setSpacing(20)

        title = QLabel("Settings")
        title.setObjectName("page_title")
        layout.addWidget(title)

        subtitle = QLabel("Configure application preferences")
        subtitle.setObjectName("page_subtitle")
        layout.addWidget(subtitle)

        # ─── Network Settings ───────────────────
        net_group = QGroupBox("🌐  Network")
        net_form = QFormLayout(net_group)
        net_form.setSpacing(12)

        self._scan_timeout = QSpinBox()
        self._scan_timeout.setButtonSymbols(QSpinBox.NoButtons)
        self._scan_timeout.setRange(1, 30)
        self._scan_timeout.setValue(1)
        self._scan_timeout.setSuffix(" seconds")
        net_form.addRow("Scan Timeout:", self._scan_timeout)

        self._default_port = QSpinBox()
        self._default_port.setButtonSymbols(QSpinBox.NoButtons)
        self._default_port.setRange(1, 65535)
        self._default_port.setValue(5000)
        net_form.addRow("Default TCP Port:", self._default_port)

        self._udp_port = QSpinBox()
        self._udp_port.setButtonSymbols(QSpinBox.NoButtons)
        self._udp_port.setRange(1, 65535)
        self._udp_port.setValue(5001)
        net_form.addRow("Default UDP Port:", self._udp_port)

        self._scan_threads = QSpinBox()
        self._scan_threads.setButtonSymbols(QSpinBox.NoButtons)
        self._scan_threads.setRange(10, 200)
        self._scan_threads.setValue(50)
        net_form.addRow("Scan Threads:", self._scan_threads)

        layout.addWidget(net_group)

        # ─── Appearance ─────────────────────────
        appearance_group = QGroupBox("🎨  Appearance")
        appearance_form = QFormLayout(appearance_group)
        appearance_form.setSpacing(12)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["dark", "light"])
        self._theme_combo.currentTextChanged.connect(self._on_theme_changed)
        appearance_form.addRow("Theme:", self._theme_combo)

        layout.addWidget(appearance_group)

        # ─── Logging ────────────────────────────
        log_group = QGroupBox("📋  Logging")
        log_form = QFormLayout(log_group)
        log_form.setSpacing(12)

        self._log_level = QComboBox()
        self._log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self._log_level.setCurrentText("INFO")
        log_form.addRow("Log Level:", self._log_level)

        clear_logs_btn = QPushButton("🗑️ Clear All Logs")
        clear_logs_btn.setObjectName("danger_button")
        clear_logs_btn.clicked.connect(self._clear_logs)
        log_form.addRow("", clear_logs_btn)

        layout.addWidget(log_group)

        # ─── Database ───────────────────────────
        db_group = QGroupBox("🗄️  Database")
        db_form = QFormLayout(db_group)
        db_form.setSpacing(12)

        db_path_label = QLabel(self._db.db_path)
        db_path_label.setWordWrap(True)
        db_form.addRow("Path:", db_path_label)

        backup_btn = QPushButton("💾 Backup Database")
        backup_btn.setObjectName("secondary_button")
        backup_btn.clicked.connect(self._backup_database)
        db_form.addRow("", backup_btn)

        layout.addWidget(db_group)

        # ─── Save Button ────────────────────────
        save_row = QHBoxLayout()
        save_row.addStretch()
        save_btn = QPushButton("💾  Save Settings")
        save_btn.setMinimumWidth(200)
        save_btn.clicked.connect(self._save_settings)
        save_row.addWidget(save_btn)
        save_row.addStretch()
        layout.addLayout(save_row)

        layout.addStretch()

        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _load_settings(self) -> None:
        """Load settings from database."""
        try:
            self._scan_timeout.setValue(
                int(self._settings_repo.get("scan_timeout", "1"))
            )
            self._default_port.setValue(
                int(self._settings_repo.get("tcp_port", "5000"))
            )
            self._udp_port.setValue(
                int(self._settings_repo.get("udp_port", "5001"))
            )
            self._scan_threads.setValue(
                int(self._settings_repo.get("scan_threads", "50"))
            )
            self._theme_combo.setCurrentText(
                self._settings_repo.get("theme", "dark")
            )
            self._log_level.setCurrentText(
                self._settings_repo.get("log_level", "INFO")
            )
        except Exception as e:
            logger.error("Error loading settings: %s", e)

    def _save_settings(self) -> None:
        """Save settings to database."""
        try:
            self._settings_repo.set(
                "scan_timeout", str(self._scan_timeout.value()), "network"
            )
            self._settings_repo.set(
                "tcp_port", str(self._default_port.value()), "network"
            )
            self._settings_repo.set(
                "udp_port", str(self._udp_port.value()), "network"
            )
            self._settings_repo.set(
                "scan_threads", str(self._scan_threads.value()), "network"
            )
            self._settings_repo.set(
                "theme", self._theme_combo.currentText(), "appearance"
            )
            self._settings_repo.set(
                "log_level", self._log_level.currentText(), "logging"
            )

            # Apply log level
            log_level = self._log_level.currentText()
            logging.getLogger().setLevel(getattr(logging, log_level))

            self.show_toast.emit("Settings saved successfully", "success")
            logger.info("Settings saved")

        except Exception as e:
            self.show_toast.emit(f"Failed to save settings: {str(e)}", "error")
            logger.error("Error saving settings: %s", e)

    def _on_theme_changed(self, theme: str) -> None:
        """Handle theme selection change."""
        self.theme_changed.emit(theme)

    def _clear_logs(self) -> None:
        """Clear all logs with confirmation."""
        reply = QMessageBox.question(
            self, "Clear Logs",
            "Are you sure you want to clear all logs?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            from utils.logger import memory_handler
            memory_handler.clear()
            logger.info("Logs cleared from settings")
            self.show_toast.emit("Logs cleared", "success")

    def _backup_database(self) -> None:
        """Create a database backup."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"lan_manager_backup_{timestamp}.db"

        path, _ = QFileDialog.getSaveFileName(
            self, "Backup Database", default_name,
            "SQLite Database (*.db)"
        )
        if not path:
            return

        if self._db.backup(path):
            self.show_toast.emit(f"Database backed up to {path}", "success")
        else:
            self.show_toast.emit("Backup failed", "error")

    def refresh(self) -> None:
        """Reload settings."""
        self._load_settings()

    def cleanup(self) -> None:
        pass
