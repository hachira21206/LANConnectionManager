"""Logs page with filtering, search, and export."""
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QLineEdit, QHeaderView, QAbstractItemView,
    QFileDialog, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont

from services.monitoring_service import MonitoringService
from utils.logger import memory_handler

logger = logging.getLogger(__name__)

# Level colors (Cyber Dark palette)
LEVEL_COLORS = {
    'DEBUG':   '#3a5a7a',
    'INFO':    '#00d4ff',
    'WARNING': '#ff8c00',
    'ERROR':   '#ff3333',
}


class LogsPage(QWidget):
    """Application logs viewer page."""

    show_toast = Signal(str, str)

    def __init__(self, monitoring_service: MonitoringService, parent=None):
        super().__init__(parent)
        self._mon_service = monitoring_service
        self._setup_ui()

        # Track last known record count for incremental updates
        self._last_record_count = 0

        # Auto-refresh timer
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._incremental_load)
        self._refresh_timer.start(3000)

    def _setup_ui(self) -> None:
        """Build logs page layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 24)
        layout.setSpacing(12)

        title = QLabel("System Logs")
        title.setObjectName("page_title")
        layout.addWidget(title)

        subtitle = QLabel("app.events | diagnostics | audit.trail")
        subtitle.setObjectName("page_subtitle")
        layout.addWidget(subtitle)

        # Controls
        controls = QHBoxLayout()

        self._level_filter = QComboBox()
        self._level_filter.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR"])
        self._level_filter.currentIndexChanged.connect(self._load_logs)
        controls.addWidget(self._level_filter)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍 Search logs...")
        self._search_input.textChanged.connect(self._filter_logs)
        controls.addWidget(self._search_input)

        controls.addStretch()

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setObjectName("secondary_button")
        refresh_btn.clicked.connect(self._load_logs)
        controls.addWidget(refresh_btn)

        export_btn = QPushButton("📥 Export")
        export_btn.setObjectName("secondary_button")
        export_btn.clicked.connect(self._export_logs)
        controls.addWidget(export_btn)

        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.setObjectName("danger_button")
        clear_btn.clicked.connect(self._clear_logs)
        controls.addWidget(clear_btn)

        layout.addLayout(controls)

        # Log count
        self._count_label = QLabel("0 entries")
        layout.addWidget(self._count_label)

        # Table
        self._table = QTableWidget()
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSortingEnabled(True)
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels([
            "Timestamp", "Level", "Module", "Message"
        ])

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

        layout.addWidget(self._table, 1)

    def _load_logs(self) -> None:
        """Full reload of logs from in-memory handler."""
        level = self._level_filter.currentText()
        records = memory_handler.get_records(
            level if level != "ALL" else None
        )

        self._table.setSortingEnabled(False)
        self._table.setRowCount(0)

        mono_font = QFont()
        mono_font.setFamilies(["JetBrains Mono", "Cascadia Code", "Consolas"])
        mono_font.setPointSize(11)

        for record in reversed(records):  # Most recent first
            self._append_log_row(record, mono_font)

        self._table.setSortingEnabled(True)
        self._last_record_count = len(records)
        self._count_label.setText(f"{self._table.rowCount()} entries")

    def _incremental_load(self) -> None:
        """Append only new log records since last refresh."""
        level = self._level_filter.currentText()
        records = memory_handler.get_records(
            level if level != "ALL" else None
        )
        new_count = len(records)

        if new_count == self._last_record_count:
            return  # No new records

        if new_count < self._last_record_count:
            # Records were cleared or filtered differently, do full reload
            self._load_logs()
            return

        # Only new records (they are at the end of the list)
        new_records = records[self._last_record_count:]

        mono_font = QFont()
        mono_font.setFamilies(["JetBrains Mono", "Cascadia Code", "Consolas"])
        mono_font.setPointSize(11)

        self._table.setSortingEnabled(False)
        for record in reversed(new_records):  # Most recent first → insert at top
            self._table.insertRow(0)
            self._set_log_row(0, record, mono_font)
        self._table.setSortingEnabled(True)

        self._last_record_count = new_count
        self._count_label.setText(f"{self._table.rowCount()} entries")

    def _append_log_row(self, record: dict, mono_font: QFont) -> None:
        """Append a log record as a new row at the end of the table."""
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._set_log_row(row, record, mono_font)

    def _set_log_row(self, row: int, record: dict, mono_font: QFont) -> None:
        """Set cell items for a log row."""
        ts_item = QTableWidgetItem(record.get('timestamp', ''))
        ts_item.setFont(mono_font)
        ts_item.setForeground(QColor("#3a5a7a"))
        self._table.setItem(row, 0, ts_item)

        level_text = record.get('level', '')
        level_item = QTableWidgetItem(level_text)
        color = LEVEL_COLORS.get(level_text, '#cce0ff')
        level_item.setForeground(QColor(color))
        level_item.setFont(mono_font)
        self._table.setItem(row, 1, level_item)

        module_item = QTableWidgetItem(record.get('module', ''))
        module_item.setFont(mono_font)
        module_item.setForeground(QColor("#5a7a9a"))
        self._table.setItem(row, 2, module_item)

        msg_item = QTableWidgetItem(record.get('message', ''))
        if level_text in ('WARNING', 'ERROR'):
            msg_item.setForeground(QColor(LEVEL_COLORS.get(level_text)))
        self._table.setItem(row, 3, msg_item)

    def _filter_logs(self) -> None:
        """Filter table by search text."""
        search = self._search_input.text().lower()
        for row in range(self._table.rowCount()):
            match = False
            for col in range(self._table.columnCount()):
                item = self._table.item(row, col)
                if item and search in item.text().lower():
                    match = True
                    break
            self._table.setRowHidden(row, not match if search else False)

    def _export_logs(self) -> None:
        """Export logs to a text file."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Logs", "logs.txt", "Text Files (*.txt)"
        )
        if not path:
            return

        try:
            with open(path, 'w', encoding='utf-8') as f:
                records = memory_handler.get_records()
                for record in records:
                    f.write(
                        f"{record['timestamp']} | {record['level']:8s} | "
                        f"{record['module']:15s} | {record['message']}\n"
                    )
            self.show_toast.emit(f"Logs exported to {path}", "success")
        except Exception as e:
            self.show_toast.emit(f"Export failed: {str(e)}", "error")

    def _clear_logs(self) -> None:
        """Clear all logs."""
        memory_handler.clear()
        self._mon_service.clear_logs()
        self._table.setRowCount(0)
        self._last_record_count = 0
        self._count_label.setText("0 entries")
        logger.info("Logs cleared by user")

    def refresh(self) -> None:
        """Refresh logs."""
        self._load_logs()

    def cleanup(self) -> None:
        self._refresh_timer.stop()
