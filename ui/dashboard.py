"""Dashboard page with network overview and statistics cards."""
import logging
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, Signal

from services.device_service import DeviceService
from services.monitoring_service import MonitoringService
from network.traffic_monitor import TrafficMonitor
from network.network_utils import (
    get_local_ip, get_active_interface, get_subnet_info, get_default_gateway
)
from utils.helpers import format_bytes, format_speed

logger = logging.getLogger(__name__)


class StatCard(QFrame):
    """A statistics display card widget with accent color."""

    def __init__(self, title: str, value: str = "0",
                 accent: str = "#00d4ff", parent=None):
        super().__init__(parent)
        self.setObjectName("stat_card")
        self.setMinimumWidth(180)
        self.setMinimumHeight(100)
        self._accent = accent

        # Accent colored top border line
        top_strip = QFrame()
        top_strip.setFixedHeight(3)
        top_strip.setStyleSheet(f"background-color: {accent}; border-radius: 2px;")

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        inner = QWidget()
        inner.setStyleSheet("background-color: transparent;")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setSpacing(4)
        inner_layout.setContentsMargins(16, 12, 16, 16)

        # Top row: title only
        title_label = QLabel(title.upper())
        title_label.setObjectName("card_title")
        inner_layout.addWidget(title_label)

        # Value
        self._value_label = QLabel(value)
        self._value_label.setObjectName("card_value")
        self._value_label.setStyleSheet(f"background-color: transparent; color: {accent};")
        # Ensure label has enough height to render the large font without clipping
        self._value_label.setMinimumHeight(45)
        self._value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        inner_layout.addWidget(self._value_label)

        layout.addWidget(top_strip)
        layout.addWidget(inner)

    def set_value(self, value: str) -> None:
        """Update the displayed value."""
        self._value_label.setText(value)


class InfoRow(QFrame):
    """A key-value information row with smart font selection."""

    # Keys that should use monospace font
    MONO_KEYS = {"IPv4 Address", "Subnet Mask", "Gateway", "Network", "CIDR"}

    def __init__(self, key: str, value: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)

        key_label = QLabel(key.upper())
        key_label.setObjectName("card_title")
        key_label.setFixedWidth(140)
        layout.addWidget(key_label)

        self._value_label = QLabel(value or "—")
        # Use IP label style for technical data
        if key in self.MONO_KEYS:
            self._value_label.setObjectName("ip_label")
        else:
            self._value_label.setObjectName("card_value_small")
        layout.addWidget(self._value_label, 1)

    def set_value(self, value: str) -> None:
        self._value_label.setText(value or "—")


class DashboardPage(QWidget):
    """Dashboard with network overview and statistics."""

    show_toast = Signal(str, str)

    def __init__(self, device_service: DeviceService,
                 monitoring_service: MonitoringService,
                 traffic_monitor: TrafficMonitor,
                 parent=None):
        super().__init__(parent)
        self._device_service = device_service
        self._monitoring_service = monitoring_service
        self._traffic_monitor = traffic_monitor

        self._setup_ui()
        self._connect_signals()

        # Cache for network info (refreshed less frequently)
        self._cached_iface = None
        self._cached_gateway = None
        self._net_refresh_counter = 0
        self._NET_REFRESH_INTERVAL = 12  # Refresh network info every 12 * 5s = 60s

        # Auto-refresh timer
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.refresh)
        self._refresh_timer.start(5000)  # Refresh every 5 seconds

    def _setup_ui(self) -> None:
        """Build dashboard layout."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 0, 24, 24)
        layout.setSpacing(20)

        # Page header
        title = QLabel("Dashboard")
        title.setObjectName("page_title")
        layout.addWidget(title)

        subtitle = QLabel("network.overview | realtime.stats | auto_refresh=5s")
        subtitle.setObjectName("page_subtitle")
        layout.addWidget(subtitle)

        # ─── Network Info Card ──────────────────
        net_card = QFrame()
        net_card.setObjectName("card")
        net_layout = QVBoxLayout(net_card)

        net_title = QLabel("-- NETWORK OVERVIEW --")
        net_title.setObjectName("page_subtitle")
        net_layout.addWidget(net_title)

        # Network info rows
        info_grid = QGridLayout()
        info_grid.setSpacing(8)

        self._info_rows = {}
        fields = [
            ("Interface", ""), ("IPv4 Address", ""),
            ("Subnet Mask", ""), ("Gateway", ""),
            ("Network", ""), ("CIDR", ""),
        ]

        for i, (key, val) in enumerate(fields):
            row = InfoRow(key, val)
            self._info_rows[key] = row
            info_grid.addWidget(row, i // 2, i % 2)

        net_layout.addLayout(info_grid)
        layout.addWidget(net_card)

        # ─── Statistics Cards ───────────────────
        stats_label = QLabel("-- SYSTEM METRICS --")
        stats_label.setObjectName("page_subtitle")
        layout.addWidget(stats_label)

        # Row 1: Device stats
        row1 = QHBoxLayout()
        row1.setSpacing(16)

        self._total_card = StatCard("Total Devices", "0", "#00d4ff")
        self._online_card = StatCard("Online", "0", "#00ff88")
        self._offline_card = StatCard("Offline", "0", "#ff3333")
        self._active_card = StatCard("Active Connections", "0", "#b8a0ff")

        row1.addWidget(self._total_card)
        row1.addWidget(self._online_card)
        row1.addWidget(self._offline_card)
        row1.addWidget(self._active_card)
        layout.addLayout(row1)

        # Row 2: Connection & Traffic stats
        row2 = QHBoxLayout()
        row2.setSpacing(16)

        self._tcp_card = StatCard("TCP Connections", "0", "#00d4ff")
        self._udp_card = StatCard("UDP Connections", "0", "#7a9cbf")
        self._download_card = StatCard("Download Speed", "0 B/s", "#00d4ff")
        self._upload_card = StatCard("Upload Speed", "0 B/s", "#00ff88")

        row2.addWidget(self._tcp_card)
        row2.addWidget(self._udp_card)
        row2.addWidget(self._download_card)
        row2.addWidget(self._upload_card)
        layout.addLayout(row2)

        # Row 3: Total traffic
        row3 = QHBoxLayout()
        row3.setSpacing(16)

        self._bytes_sent_card = StatCard("Total Sent", "0 B", "#ff8c00")
        self._bytes_recv_card = StatCard("Total Received", "0 B", "#00d4ff")
        self._pkts_sent_card = StatCard("Packets Sent", "0", "#ff8c00")
        self._pkts_recv_card = StatCard("Packets Received", "0", "#00d4ff")

        row3.addWidget(self._bytes_sent_card)
        row3.addWidget(self._bytes_recv_card)
        row3.addWidget(self._pkts_sent_card)
        row3.addWidget(self._pkts_recv_card)
        layout.addLayout(row3)

        layout.addStretch()

        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _connect_signals(self) -> None:
        """Connect traffic monitor signals."""
        self._traffic_monitor.stats_updated.connect(self._update_traffic)

    def _update_traffic(self, stats) -> None:
        """Update traffic cards with real-time data."""
        self._download_card.set_value(format_speed(stats.download_speed))
        self._upload_card.set_value(format_speed(stats.upload_speed))
        self._bytes_sent_card.set_value(format_bytes(stats.bytes_sent))
        self._bytes_recv_card.set_value(format_bytes(stats.bytes_recv))
        self._pkts_sent_card.set_value(f"{stats.packets_sent:,}")
        self._pkts_recv_card.set_value(f"{stats.packets_recv:,}")

    def refresh(self) -> None:
        """Refresh all dashboard data."""
        # Network info (refreshed less frequently since it rarely changes)
        self._net_refresh_counter += 1
        if self._cached_iface is None or self._net_refresh_counter >= self._NET_REFRESH_INTERVAL:
            self._net_refresh_counter = 0
            try:
                self._cached_iface = get_active_interface()
                if self._cached_iface:
                    ip = self._cached_iface.get('ipv4', '')
                    mask = self._cached_iface.get('netmask', '')
                    if ip and mask:
                        self._cached_gateway = get_default_gateway()
            except Exception as e:
                logger.debug("Dashboard network info refresh error: %s", e)

        try:
            iface = self._cached_iface
            if iface:
                self._info_rows["Interface"].set_value(iface.get('name', 'N/A'))
                self._info_rows["IPv4 Address"].set_value(iface.get('ipv4', 'N/A'))
                self._info_rows["Subnet Mask"].set_value(iface.get('netmask', 'N/A'))

                ip = iface.get('ipv4', '')
                mask = iface.get('netmask', '')
                if ip and mask:
                    info = get_subnet_info(ip, mask)
                    self._info_rows["Network"].set_value(info.get('network', 'N/A'))
                    self._info_rows["CIDR"].set_value(info.get('cidr', 'N/A'))
                    self._info_rows["Gateway"].set_value(
                        self._cached_gateway or 'N/A'
                    )
        except Exception as e:
            logger.debug("Dashboard network info error: %s", e)

        # Device stats
        try:
            stats = self._device_service.get_statistics()
            self._total_card.set_value(str(stats['total']))
            self._online_card.set_value(str(stats['online']))
            self._offline_card.set_value(str(stats['offline']))
        except Exception as e:
            logger.debug("Dashboard device stats error: %s", e)

        # Connection stats
        try:
            conn_stats = self._monitoring_service.get_connection_stats()
            self._active_card.set_value(str(conn_stats.get('established', 0)))
            self._tcp_card.set_value(str(conn_stats.get('tcp', 0)))
            self._udp_card.set_value(str(conn_stats.get('udp', 0)))
        except Exception as e:
            logger.debug("Dashboard connection stats error: %s", e)
