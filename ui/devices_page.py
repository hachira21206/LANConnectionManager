"""Devices page with LAN scanner and device table."""
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QProgressBar, QHeaderView, QComboBox, QAbstractItemView,
    QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QBrush

from typing import Optional
from database.database import DatabaseManager
from database.repository import SettingsRepository
from services.device_service import DeviceService
from network.scanner import LANScanner
from network.network_utils import get_active_interface, get_subnet_info
from utils.validators import validate_ip, validate_subnet
from utils.helpers import format_ping

logger = logging.getLogger(__name__)


class DevicesPage(QWidget):
    """Device scanner and management page."""

    show_toast = Signal(str, str)

    def __init__(self, device_service: DeviceService, db: Optional[DatabaseManager] = None, parent=None):
        super().__init__(parent)
        self._device_service = device_service
        self._db = db or getattr(getattr(device_service, 'repo', None), 'db', None)
        self._settings_repo = SettingsRepository(self._db) if self._db else None
        self._scanner = LANScanner()
        self._is_scanning = False

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Build the devices page layout."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 0, 24, 24)
        layout.setSpacing(16)

        # Header
        title = QLabel("Devices")
        title.setObjectName("page_title")
        layout.addWidget(title)

        subtitle = QLabel("lan.scan | subnet.discovery | hostname.resolution")
        subtitle.setObjectName("page_subtitle")
        layout.addWidget(subtitle)

        # ─── Scan Controls ──────────────────────
        controls = QFrame()
        controls.setObjectName("card")
        controls_layout = QVBoxLayout(controls)

        # Scan mode
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Scan Mode:"))

        self._scan_mode = QComboBox()
        self._scan_mode.addItems([
            "Auto-detect Subnet",
            "Custom Subnet (CIDR)",
            "IP Range"
        ])
        self._scan_mode.currentIndexChanged.connect(self._on_mode_changed)
        mode_row.addWidget(self._scan_mode)
        mode_row.addStretch()
        controls_layout.addLayout(mode_row)

        # Subnet input
        self._subnet_row = QHBoxLayout()
        self._subnet_row_widget = QWidget()
        subnet_layout = QHBoxLayout(self._subnet_row_widget)
        subnet_layout.setContentsMargins(0, 0, 0, 0)
        subnet_layout.addWidget(QLabel("Subnet:"))
        self._subnet_input = QLineEdit()
        self._subnet_input.setPlaceholderText("e.g., 192.168.1.0/24")
        subnet_layout.addWidget(self._subnet_input)
        self._subnet_row_widget.setVisible(False)
        controls_layout.addWidget(self._subnet_row_widget)

        # IP range input
        self._range_row_widget = QWidget()
        range_layout = QHBoxLayout(self._range_row_widget)
        range_layout.setContentsMargins(0, 0, 0, 0)
        range_layout.addWidget(QLabel("Start IP:"))
        self._start_ip = QLineEdit()
        self._start_ip.setPlaceholderText("192.168.1.1")
        range_layout.addWidget(self._start_ip)
        range_layout.addWidget(QLabel("End IP:"))
        self._end_ip = QLineEdit()
        self._end_ip.setPlaceholderText("192.168.1.254")
        range_layout.addWidget(self._end_ip)
        self._range_row_widget.setVisible(False)
        controls_layout.addWidget(self._range_row_widget)

        # Buttons row
        btn_row = QHBoxLayout()

        self._scan_btn = QPushButton("Scan Network")
        self._scan_btn.setCursor(Qt.PointingHandCursor)
        self._scan_btn.clicked.connect(self._start_scan)
        btn_row.addWidget(self._scan_btn)

        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setObjectName("danger_button")
        self._stop_btn.setCursor(Qt.PointingHandCursor)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop_scan)
        btn_row.addWidget(self._stop_btn)

        refresh_btn = QPushButton("Refresh List")
        refresh_btn.setObjectName("secondary_button")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self._load_devices)
        btn_row.addWidget(refresh_btn)

        btn_row.addStretch()

        self._status_label = QLabel("")
        btn_row.addWidget(self._status_label)

        controls_layout.addLayout(btn_row)

        # Progress bar
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        controls_layout.addWidget(self._progress)

        layout.addWidget(controls)

        # ─── Search / Filter ────────────────────
        filter_row = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍 Search by IP, hostname, or MAC...")
        self._search_input.textChanged.connect(self._filter_table)
        filter_row.addWidget(self._search_input)

        self._status_filter = QComboBox()
        self._status_filter.addItems(["All", "Online", "Offline"])
        self._status_filter.currentIndexChanged.connect(self._filter_table)
        filter_row.addWidget(self._status_filter)

        layout.addLayout(filter_row)

        # ─── Device Table ───────────────────────
        self._table = QTableWidget()
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSortingEnabled(True)
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "Status", "IP Address", "Hostname", "MAC Address",
            "Ping", "Last Seen"
        ])

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Interactive)

        self._table.setColumnWidth(1, 140)
        self._table.setColumnWidth(3, 160)
        self._table.setColumnWidth(5, 160)

        layout.addWidget(self._table, 1)

        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _connect_signals(self) -> None:
        """Connect scanner signals."""
        self._scanner.device_found.connect(self._on_device_found)
        self._scanner.scan_progress.connect(self._on_scan_progress)
        self._scanner.scan_complete.connect(self._on_scan_complete)
        self._scanner.scan_error.connect(self._on_scan_error)
        self._scanner.scan_status.connect(self._on_scan_status)

    def _on_mode_changed(self, index: int) -> None:
        """Handle scan mode selection change."""
        self._subnet_row_widget.setVisible(index == 1)
        self._range_row_widget.setVisible(index == 2)

    def _get_scan_config(self) -> tuple[float, int]:
        """Get scan timeout and thread count from settings or defaults."""
        timeout = 1.0
        thread_count = 50
        if self._settings_repo:
            try:
                timeout = float(self._settings_repo.get("scan_timeout", "1"))
                thread_count = int(self._settings_repo.get("scan_threads", "50"))
            except (ValueError, TypeError) as e:
                logger.warning("Error reading scan settings, using defaults: %s", e)
        return timeout, thread_count

    def _start_scan(self) -> None:
        """Start network scanning."""
        if self._is_scanning:
            return

        mode = self._scan_mode.currentIndex()
        timeout, thread_count = self._get_scan_config()

        if mode == 0:
            # Auto-detect
            self._scanner.configure(timeout=timeout, thread_count=thread_count)
        elif mode == 1:
            subnet = self._subnet_input.text().strip()
            if not validate_subnet(subnet):
                self.show_toast.emit("Invalid subnet format. Use CIDR (e.g., 192.168.1.0/24)", "error")
                return
            self._scanner.configure(subnet=subnet, timeout=timeout, thread_count=thread_count)
        elif mode == 2:
            start = self._start_ip.text().strip()
            end = self._end_ip.text().strip()
            if not validate_ip(start) or not validate_ip(end):
                self.show_toast.emit("Invalid IP address format", "error")
                return
            self._scanner.configure(start_ip=start, end_ip=end,
                                    timeout=timeout, thread_count=thread_count)

        self._is_scanning = True
        self._scan_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._progress.setValue(0)
        self._progress.setVisible(True)
        self._table.setRowCount(0)

        self._device_service.mark_all_offline()
        
        self._scanner.start()
        logger.info("Scan started")

    def _stop_scan(self) -> None:
        """Stop the running scan."""
        if self._is_scanning:
            self._scanner.stop()
            self._status_label.setText("Stopping...")

    def _on_device_found(self, device) -> None:
        """Handle a discovered device."""
        self._device_service.save_device(device)
        self._add_device_to_table(device)

    def _on_scan_progress(self, current: int, total: int) -> None:
        """Update progress bar."""
        self._progress.setMaximum(total)
        self._progress.setValue(current)

    def _on_scan_complete(self, devices: list) -> None:
        """Handle scan completion."""
        self._is_scanning = False
        self._scan_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._progress.setVisible(False)
        
        # Load all devices (both online and offline) from DB to update the table
        self._load_devices()
        
        self._status_label.setText(
            f"Scan complete. Found {len(devices)} device(s) online."
        )

    def _on_scan_error(self, error: str) -> None:
        """Handle scan error."""
        self._is_scanning = False
        self._scan_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._progress.setVisible(False)
        self._status_label.setText(f"Error: {error}")
        self.show_toast.emit(error, "error")

    def _on_scan_status(self, status: str) -> None:
        """Update status label."""
        self._status_label.setText(status)

    def _add_device_to_table(self, device) -> None:
        """Add a device row to the table with color coding."""
        row = self._table.rowCount()
        self._table.insertRow(row)

        is_online = device.is_online

        # Row background color based on status
        row_bg_online = QColor(0, 255, 136, 18)   # Neon green very subtle
        row_bg_offline = QColor(255, 51, 51, 15)   # Red very subtle
        row_bg = row_bg_online if is_online else row_bg_offline

        mono_font = QFont("JetBrains Mono")
        mono_font.setFamilies(["JetBrains Mono", "Cascadia Code", "Consolas"])
        mono_font.setPointSize(11)

        # Status badge
        status_text = "ONLINE" if is_online else "OFFLINE"
        status_item = QTableWidgetItem(status_text)
        status_item.setTextAlignment(Qt.AlignCenter)
        if is_online:
            status_item.setForeground(QBrush(QColor("#00ff88")))
        else:
            status_item.setForeground(QBrush(QColor("#ff3333")))
        status_item.setBackground(QBrush(row_bg))
        self._table.setItem(row, 0, status_item)

        # IP Address (monospace + cyan)
        ip_item = QTableWidgetItem(device.ip_address)
        ip_item.setFont(mono_font)
        ip_item.setForeground(QBrush(QColor("#00d4ff")))
        ip_item.setBackground(QBrush(row_bg))
        self._table.setItem(row, 1, ip_item)

        # Hostname
        hostname_item = QTableWidgetItem(device.hostname or "N/A")
        hostname_item.setBackground(QBrush(row_bg))
        self._table.setItem(row, 2, hostname_item)

        # MAC Address (monospace + muted)
        mac_item = QTableWidgetItem(device.mac_address or "N/A")
        mac_item.setFont(mono_font)
        mac_item.setForeground(QBrush(QColor("#7a9cbf")))
        mac_item.setBackground(QBrush(row_bg))
        self._table.setItem(row, 3, mac_item)

        # Ping — color coded by latency
        ping_text = format_ping(device.response_time)
        ping_item = QTableWidgetItem(ping_text)
        ping_item.setTextAlignment(Qt.AlignCenter)
        ping_item.setFont(mono_font)
        try:
            # Extract numeric value for color coding
            rt = float(device.response_time) if device.response_time else None
            if rt is not None:
                if rt < 50:
                    ping_item.setForeground(QBrush(QColor("#00ff88")))  # Good
                elif rt < 200:
                    ping_item.setForeground(QBrush(QColor("#ff8c00")))  # Warn
                else:
                    ping_item.setForeground(QBrush(QColor("#ff3333")))  # Bad
            else:
                ping_item.setForeground(QBrush(QColor("#5a7a9a")))
        except (TypeError, ValueError):
            ping_item.setForeground(QBrush(QColor("#5a7a9a")))
        ping_item.setBackground(QBrush(row_bg))
        self._table.setItem(row, 4, ping_item)

        # Last Seen
        last_seen_item = QTableWidgetItem(device.last_seen or "N/A")
        last_seen_item.setForeground(QBrush(QColor("#5a7a9a")))
        last_seen_item.setBackground(QBrush(row_bg))
        self._table.setItem(row, 5, last_seen_item)

    def _load_devices(self) -> None:
        """Load devices from database into table."""
        self._table.setRowCount(0)
        devices = self._device_service.get_all_devices()
        for device in devices:
            self._add_device_to_table(device)
        self._status_label.setText(f"{len(devices)} device(s) in database")

    def _filter_table(self) -> None:
        """Filter table rows based on search and status filter."""
        search = self._search_input.text().lower()
        status_filter = self._status_filter.currentText()

        for row in range(self._table.rowCount()):
            show = True

            # Status filter
            if status_filter != "All":
                status_item = self._table.item(row, 0)
                if status_item:
                    if status_filter == "Online" and "ONLINE" not in status_item.text():
                        show = False
                    elif status_filter == "Offline" and "OFFLINE" not in status_item.text():
                        show = False

            # Text search
            if show and search:
                match = False
                for col in range(self._table.columnCount()):
                    item = self._table.item(row, col)
                    if item and search in item.text().lower():
                        match = True
                        break
                show = match

            self._table.setRowHidden(row, not show)

    def refresh(self) -> None:
        """Refresh the page data."""
        if not self._is_scanning:
            self._load_devices()

    def cleanup(self) -> None:
        """Stop scanner if running."""
        if self._is_scanning:
            self._scanner.stop()
            self._scanner.wait(3000)
