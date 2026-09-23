import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from app.config import config
from utils.logger import setup_logging
from database.database import DatabaseManager
from ui.main_window import MainWindow


def main():
    """Application entry point."""
    # Initialize logging
    setup_logging(config.log_file, config.log_level)
    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("LAN Connection Manager v%s starting...", config.app_version)
    logger.info("=" * 50)

    # Initialize database
    try:
        db = DatabaseManager.get_instance(config.db_path)
        logger.info("Database initialized: %s", config.db_path)
    except Exception as e:
        logger.critical("Failed to initialize database: %s", e)
        sys.exit(1)

    # Load saved settings
    try:
        from database.repository import SettingsRepository
        settings_repo = SettingsRepository(db)
        saved_theme = settings_repo.get("theme", "dark")
        config.theme = saved_theme
        saved_log_level = settings_repo.get("log_level", "INFO")
        if saved_log_level:
            logging.getLogger().setLevel(getattr(logging, saved_log_level, logging.INFO))
    except Exception:
        pass

    # Create Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName(config.app_name)
    app.setApplicationVersion(config.app_version)

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Create and show main window
    try:
        window = MainWindow()
        window.show()
        logger.info("Application window displayed")
    except Exception as e:
        logger.critical("Failed to create main window: %s", e)
        sys.exit(1)

    # Run event loop
    exit_code = app.exec()

    logger.info("Application exiting with code %d", exit_code)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
