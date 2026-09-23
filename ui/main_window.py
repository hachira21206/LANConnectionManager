"""Main window with sidebar navigation and stacked content pages."""
import logging
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame,
    QStatusBar, QApplication
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QRect
from PySide6.QtGui import QFont, QIcon

from app.config import config
from app.constants import NAV_ITEMS, DARK_THEME, LIGHT_THEME
from network.network_utils import get_local_ip, get_active_interface
from database.database import DatabaseManager
from services.device_service import DeviceService
from services.connection_service import ConnectionService
from services.monitoring_service import MonitoringService
from network.traffic_monitor import TrafficMonitor

from ui.dashboard import DashboardPage
from ui.devices_page import DevicesPage
from ui.connections_page import ConnectionsPage
from ui.monitor_page import MonitorPage
from ui.logs_page import LogsPage
from ui.settings_page import SettingsPage

logger = logging.getLogger(__name__)


class ToastNotification(QFrame):
    """Animated toast notification widget."""

    def __init__(self, parent, message: str, toast_type: str = "info"):
        super().__init__(parent)
        self.setObjectName(f"toast_{toast_type}")
        self.setFixedHeight(50)
        self.setMinimumWidth(300)
        self.setMaximumWidth(450)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)

        icons = {"success": "✅", "error": "❌", "warning": "⚠️", "info": "ℹ️"}
        icon_label = QLabel(icons.get(toast_type, "ℹ️"))
        icon_label.setFont(QFont("Segoe UI Emoji", 14))
        layout.addWidget(icon_label)

        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label, 1)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("icon_button")
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self._hide_toast)
        layout.addWidget(close_btn)

        # Auto-hide timer
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._hide_toast)
        self._timer.start(4000)

    def _hide_toast(self):
        self.setVisible(False)
        self.deleteLater()


class MainWindow(QMainWindow):
    """Main application window with sidebar navigation."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"LAN Connection Manager  [LIVE]")
        self.setMinimumSize(1100, 720)
        self.resize(config.window_width, config.window_height)

        # Initialize services
        self.db = DatabaseManager.get_instance(config.db_path)
        self.device_service = DeviceService(self.db)
        self.connection_service = ConnectionService(self.db)
        self.monitoring_service = MonitoringService(self.db)
        self.traffic_monitor = TrafficMonitor()

        # Current theme
        self._current_theme = config.theme

        # Build UI
        self._setup_ui()
        self._apply_theme(self._current_theme)
        self._connect_signals()

        # Start traffic monitor
        self.traffic_monitor.configure(interval=1.0)
        self.traffic_monitor.start()

        # Log startup
        self.monitoring_service.log_event(
            "INFO", "main", "Application started"
        )
        logger.info("Main window initialized")

    def _setup_ui(self) -> None:
        """Build the main window layout."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ─── Sidebar ────────────────────────────
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # App title
        title = QLabel("LAN MANAGER")
        title.setObjectName("sidebar_title")
        sidebar_layout.addWidget(title)

        subtitle = QLabel(f"v{config.app_version}  |  SYSADMIN")
        subtitle.setObjectName("sidebar_subtitle")
        sidebar_layout.addWidget(subtitle)

        # Separator
        sep1 = QFrame()
        sep1.setObjectName("sidebar_separator")
        sep1.setFrameShape(QFrame.HLine)
        sidebar_layout.addWidget(sep1)

        # Navigation buttons
        self._nav_buttons: dict[str, QPushButton] = {}
        for key, label in NAV_ITEMS:
            btn = QPushButton(f"  {label}")
            btn.setObjectName("nav_button")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty("active", False)
            btn.clicked.connect(lambda checked, k=key: self._navigate(k))
            sidebar_layout.addWidget(btn)
            self._nav_buttons[key] = btn

        sidebar_layout.addStretch()

        # Separator before footer
        sep2 = QFrame()
        sep2.setObjectName("sidebar_separator")
        sep2.setFrameShape(QFrame.HLine)
        sidebar_layout.addWidget(sep2)

        # Host info section
        host_label = QLabel("HOST MACHINE")
        host_label.setObjectName("sidebar_host_label")
        sidebar_layout.addWidget(host_label)

        self._host_ip_label = QLabel("...")
        self._host_ip_label.setObjectName("sidebar_host_ip")
        sidebar_layout.addWidget(self._host_ip_label)
        self._update_host_ip()

        # Add some padding at the bottom
        bottom_spacer = QWidget()
        bottom_spacer.setFixedHeight(16)
        sidebar_layout.addWidget(bottom_spacer)

        main_layout.addWidget(sidebar)

        # ─── Content Area ───────────────────────
        content_area = QFrame()
        content_area.setObjectName("content_area")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Stacked widget for pages
        self._stack = QStackedWidget()
        self._pages: dict[str, QWidget] = {}

        # Create pages
        self._pages['dashboard'] = DashboardPage(
            self.device_service, self.monitoring_service, self.traffic_monitor
        )
        self._pages['devices'] = DevicesPage(self.device_service)
        self._pages['connections'] = ConnectionsPage(
            self.connection_service, self.monitoring_service
        )
        self._pages['monitor'] = MonitorPage(self.traffic_monitor)
        self._pages['logs'] = LogsPage(self.monitoring_service)
        self._pages['settings'] = SettingsPage(self.db)

        for page in self._pages.values():
            self._stack.addWidget(page)

        content_layout.addWidget(self._stack)
        main_layout.addWidget(content_area, 1)

        # ─── Status Bar ─────────────────────────
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        try:
            iface = get_active_interface()
            if iface:
                status_bar.showMessage(
                    f"  ●  ONLINE  │  IF: {iface.get('name','N/A')}  │  IP: {iface.get('ipv4','N/A')}  │  NET: {iface.get('netmask','N/A')}"
                )
            else:
                status_bar.showMessage("  ●  Ready")
        except Exception:
            status_bar.showMessage("  ●  Ready")

        # Navigate to dashboard by default
        self._navigate("dashboard")

    def _connect_signals(self) -> None:
        """Connect inter-page signals."""
        # Settings page theme change
        settings_page = self._pages.get('settings')
        if settings_page and hasattr(settings_page, 'theme_changed'):
            settings_page.theme_changed.connect(self._apply_theme)

        # Connect toast signals from pages
        for page in self._pages.values():
            if hasattr(page, 'show_toast') and getattr(page, 'show_toast') is not None:
                try:
                    page.show_toast.connect(self._show_toast)
                except Exception:
                    pass

    def _navigate(self, key: str) -> None:
        """Navigate to a page.

        Args:
            key: Page key from NAV_ITEMS.
        """
        if key in self._pages:
            self._stack.setCurrentWidget(self._pages[key])

            # Update active state
            for k, btn in self._nav_buttons.items():
                btn.setProperty("active", k == key)
                btn.style().unpolish(btn)
                btn.style().polish(btn)

            # Refresh page data
            page = self._pages[key]
            if hasattr(page, 'refresh'):
                page.refresh()

            self.statusBar().showMessage(
                f"Page: {key.capitalize()}"
            )

    def _update_host_ip(self) -> None:
        """Update host IP display in sidebar."""
        try:
            iface = get_active_interface()
            if iface:
                self._host_ip_label.setText(
                    f"  {iface.get('ipv4', 'N/A')}"
                )
            else:
                self._host_ip_label.setText("  N/A")
        except Exception:
            self._host_ip_label.setText("  N/A")

    def _apply_theme(self, theme: str) -> None:
        """Apply a theme stylesheet.

        Args:
            theme: 'dark' or 'light'.
        """
        self._current_theme = theme
        stylesheet = DARK_THEME if theme == "dark" else LIGHT_THEME
        QApplication.instance().setStyleSheet(stylesheet)

        self._update_host_ip()

        # Save preference
        from database.repository import SettingsRepository
        try:
            settings_repo = SettingsRepository(self.db)
            settings_repo.set("theme", theme, "appearance")
        except Exception:
            pass

        logger.info("Theme changed to %s", theme)

    def _show_toast(self, message: str, toast_type: str = "info") -> None:
        """Show a toast notification.

        Args:
            message: Notification message.
            toast_type: 'success', 'error', 'warning', 'info'.
        """
        toast = ToastNotification(self, message, toast_type)
        toast.setParent(self)

        # Position toast at top-right
        x = self.width() - toast.width() - 20
        y = 20
        toast.move(x, y)
        toast.show()
        toast.raise_()

    def resizeEvent(self, event) -> None:
        """Handle window resize."""
        super().resizeEvent(event)

    def closeEvent(self, event) -> None:
        """Clean up on close."""
        logger.info("Application closing...")

        # Stop traffic monitor
        if self.traffic_monitor.is_running:
            self.traffic_monitor.stop()
            self.traffic_monitor.wait(2000)

        # Stop any running services in pages
        for page in self._pages.values():
            if hasattr(page, 'cleanup'):
                page.cleanup()

        # Log shutdown
        self.monitoring_service.log_event(
            "INFO", "main", "Application closed"
        )

        # Close database
        self.db.close()

        event.accept()
