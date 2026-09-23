"""Network monitor page with real-time traffic charts."""
import logging
from collections import deque

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QComboBox, QGridLayout, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, QRectF, Signal
from PySide6.QtGui import QPainter, QPen, QColor, QLinearGradient, QPainterPath, QFont, QBrush

from network.traffic_monitor import TrafficMonitor
from utils.helpers import format_bytes, format_speed

logger = logging.getLogger(__name__)


class TrafficChart(QWidget):
    """Custom widget that draws a real-time line chart using QPainter."""

    def __init__(self, title: str = "Chart", color: str = "#58a6ff",
                 parent=None):
        super().__init__(parent)
        self.setMinimumHeight(180)
        self._title = title
        self._color = QColor(color)
        self._data: deque = deque(maxlen=60)
        self._max_value = 1.0

    def add_point(self, value: float) -> None:
        """Add a data point and refresh."""
        self._data.append(value)
        if self._data:
            self._max_value = max(max(self._data), 1.0)
        self.update()

    def clear(self) -> None:
        """Clear all data."""
        self._data.clear()
        self.update()

    def paintEvent(self, event) -> None:
        """Draw the chart with neon glow effects."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        padding = 12
        chart_x = padding + 55  # space for y-axis labels
        chart_y = padding + 24
        chart_w = w - chart_x - padding
        chart_h = h - padding * 2 - 28

        # Deep background
        painter.setPen(Qt.NoPen)
        bg_color = QColor("#070b14")
        painter.setBrush(bg_color)
        painter.drawRoundedRect(0, 0, w, h, 8, 8)

        # Chart area background (slightly lighter)
        painter.setBrush(QColor("#0a0e18"))
        painter.drawRect(int(chart_x), int(chart_y),
                         int(chart_w), int(chart_h))

        # Title
        painter.setPen(QColor("#3a5a7a"))
        painter.setFont(QFont("JetBrains Mono", 9))
        painter.drawText(int(chart_x), int(chart_y) - 8, self._title)

        # Peak value (top right)
        if self._data:
            peak = format_speed(self._max_value)
            painter.setPen(QColor("#2a4a6a"))
            painter.setFont(QFont("JetBrains Mono", 10))
            painter.drawText(
                QRectF(chart_x, chart_y - 24, chart_w, 20),
                Qt.AlignRight | Qt.AlignVCenter, f"peak: {peak}"
            )

        if len(self._data) < 2:
            painter.setPen(QColor("#1e3a5f"))
            painter.setFont(QFont("JetBrains Mono", 10))
            painter.drawText(
                QRectF(chart_x, chart_y, chart_w, chart_h),
                Qt.AlignCenter, "waiting for data..."
            )
            painter.end()
            return

        # Grid lines (dashed)
        grid_pen = QPen(QColor("#0f1e35"), 1, Qt.DashLine)
        painter.setPen(grid_pen)
        for i in range(5):
            y = chart_y + (chart_h * i / 4)
            painter.drawLine(int(chart_x), int(y),
                             int(chart_x + chart_w), int(y))

        # Vertical grid lines
        grid_pen_v = QPen(QColor("#0a1525"), 1, Qt.DotLine)
        painter.setPen(grid_pen_v)
        for i in range(1, 6):
            x = chart_x + (chart_w * i / 6)
            painter.drawLine(int(x), int(chart_y),
                             int(x), int(chart_y + chart_h))

        # Draw data line
        data_list = list(self._data)
        points = []
        step_x = chart_w / max(len(data_list) - 1, 1)

        for i, val in enumerate(data_list):
            x = chart_x + i * step_x
            y = chart_y + chart_h - (val / self._max_value * chart_h)
            points.append((x, y))

        # Fill gradient under the line
        if points:
            path = QPainterPath()
            path.moveTo(points[0][0], chart_y + chart_h)
            for x, y in points:
                path.lineTo(x, y)
            path.lineTo(points[-1][0], chart_y + chart_h)
            path.closeSubpath()

            gradient = QLinearGradient(0, chart_y, 0, chart_y + chart_h)
            fill_color = QColor(self._color)
            fill_color.setAlpha(60)
            gradient.setColorAt(0, fill_color)
            fill_color.setAlpha(4)
            gradient.setColorAt(1, fill_color)
            painter.setBrush(gradient)
            painter.setPen(Qt.NoPen)
            painter.drawPath(path)

        # Draw line (neon glow: draw twice, outer wider+faded, inner sharp)
        glow_pen = QPen(self._color, 5)
        glow_color = QColor(self._color)
        glow_color.setAlpha(40)
        glow_pen.setColor(glow_color)
        painter.setPen(glow_pen)
        for i in range(len(points) - 1):
            painter.drawLine(
                int(points[i][0]), int(points[i][1]),
                int(points[i + 1][0]), int(points[i + 1][1])
            )

        sharp_pen = QPen(self._color, 2)
        painter.setPen(sharp_pen)
        for i in range(len(points) - 1):
            painter.drawLine(
                int(points[i][0]), int(points[i][1]),
                int(points[i + 1][0]), int(points[i + 1][1])
            )

        # Glowing dot at latest point (outer glow + inner dot)
        if points:
            lx, ly = points[-1]
            # Outer glow ring
            glow = QColor(self._color)
            glow.setAlpha(50)
            painter.setBrush(QBrush(glow))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(lx) - 8, int(ly) - 8, 16, 16)
            # Middle ring
            glow.setAlpha(100)
            painter.setBrush(QBrush(glow))
            painter.drawEllipse(int(lx) - 5, int(ly) - 5, 10, 10)
            # Solid center dot
            painter.setBrush(QBrush(self._color))
            painter.drawEllipse(int(lx) - 3, int(ly) - 3, 6, 6)

        # Y-axis labels (monospace)
        painter.setPen(QColor("#2a4a6a"))
        painter.setFont(QFont("JetBrains Mono", 8))
        for i in range(5):
            y = chart_y + (chart_h * i / 4)
            val = self._max_value * (1 - i / 4)
            painter.drawText(
                int(chart_x) - 58, int(y) - 8, 54, 16,
                Qt.AlignRight | Qt.AlignVCenter,
                format_speed(val)
            )

        painter.end()


class MonitorPage(QWidget):
    """Network traffic monitoring page with real-time charts."""

    show_toast = Signal(str, str)

    def __init__(self, traffic_monitor: TrafficMonitor, parent=None):
        super().__init__(parent)
        self._monitor = traffic_monitor
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Build monitor page layout."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 0, 24, 24)
        layout.setSpacing(16)

        # Header
        title = QLabel("Network Monitor")
        title.setObjectName("page_title")
        layout.addWidget(title)

        subtitle = QLabel("realtime.traffic | bandwidth.monitor | per_interface")
        subtitle.setObjectName("page_subtitle")
        layout.addWidget(subtitle)

        # Controls
        controls = QHBoxLayout()

        controls.addWidget(QLabel("Interface:"))
        self._iface_combo = QComboBox()
        self._iface_combo.addItem("All Interfaces")
        for iface in TrafficMonitor.get_available_interfaces():
            self._iface_combo.addItem(iface)
        self._iface_combo.currentIndexChanged.connect(self._on_interface_changed)
        controls.addWidget(self._iface_combo)

        controls.addStretch()

        self._pause_btn = QPushButton("⏸️ Pause")
        self._pause_btn.setObjectName("secondary_button")
        self._pause_btn.clicked.connect(self._toggle_pause)
        controls.addWidget(self._pause_btn)

        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.setObjectName("secondary_button")
        clear_btn.clicked.connect(self._clear_data)
        controls.addWidget(clear_btn)

        layout.addLayout(controls)

        # Charts
        charts_layout = QGridLayout()
        charts_layout.setSpacing(16)

        self._download_chart = TrafficChart("DOWNLOAD", "#00d4ff")
        charts_layout.addWidget(self._download_chart, 0, 0)

        self._upload_chart = TrafficChart("UPLOAD", "#00ff88")
        charts_layout.addWidget(self._upload_chart, 0, 1)

        layout.addLayout(charts_layout)

        # Statistics cards
        stats_frame = QFrame()
        stats_frame.setObjectName("card")
        stats_layout = QGridLayout(stats_frame)
        stats_layout.setSpacing(16)

        self._stats_labels = {}
        stats_data = [
            ("Download Speed", "⬇️"), ("Upload Speed", "⬆️"),
            ("Total Received", "📥"), ("Total Sent", "📤"),
            ("Packets Received", "📬"), ("Packets Sent", "📦"),
        ]

        for i, (name, icon) in enumerate(stats_data):
            row, col = divmod(i, 3)

            frame = QFrame()
            fl = QVBoxLayout(frame)
            fl.setContentsMargins(8, 8, 8, 8)

            label = QLabel(f"{icon} {name}")
            label.setObjectName("card_title")
            fl.addWidget(label)

            value = QLabel("0")
            value.setObjectName("card_value_small")
            fl.addWidget(value)

            self._stats_labels[name] = value
            stats_layout.addWidget(frame, row, col)

        layout.addWidget(stats_frame)

        layout.addStretch()

        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _connect_signals(self) -> None:
        """Connect traffic monitor signals."""
        self._monitor.stats_updated.connect(self._update_stats)

    def _update_stats(self, stats) -> None:
        """Update charts and labels with new traffic data."""
        self._download_chart.add_point(stats.download_speed)
        self._upload_chart.add_point(stats.upload_speed)

        self._stats_labels["Download Speed"].setText(
            format_speed(stats.download_speed)
        )
        self._stats_labels["Upload Speed"].setText(
            format_speed(stats.upload_speed)
        )
        self._stats_labels["Total Received"].setText(
            format_bytes(stats.bytes_recv)
        )
        self._stats_labels["Total Sent"].setText(
            format_bytes(stats.bytes_sent)
        )
        self._stats_labels["Packets Received"].setText(
            f"{stats.packets_recv:,}"
        )
        self._stats_labels["Packets Sent"].setText(
            f"{stats.packets_sent:,}"
        )

    def _on_interface_changed(self, index: int) -> None:
        """Handle interface selection change."""
        if index == 0:
            self._monitor.set_interface(None)
        else:
            self._monitor.set_interface(self._iface_combo.currentText())

    def _toggle_pause(self) -> None:
        """Toggle pause/resume."""
        if self._monitor.is_paused:
            self._monitor.resume()
            self._pause_btn.setText("⏸️ Pause")
        else:
            self._monitor.pause()
            self._pause_btn.setText("▶️ Resume")

    def _clear_data(self) -> None:
        """Clear chart data."""
        self._download_chart.clear()
        self._upload_chart.clear()
        self._monitor.clear_history()

    def refresh(self) -> None:
        """Refresh interface list."""
        current = self._iface_combo.currentText()
        self._iface_combo.clear()
        self._iface_combo.addItem("All Interfaces")
        for iface in TrafficMonitor.get_available_interfaces():
            self._iface_combo.addItem(iface)
        idx = self._iface_combo.findText(current)
        if idx >= 0:
            self._iface_combo.setCurrentIndex(idx)

    def cleanup(self) -> None:
        """Nothing extra to clean up (monitor is stopped by main window)."""
        pass
