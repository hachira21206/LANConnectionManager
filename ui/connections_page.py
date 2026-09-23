"""Connections page with tabs for active connections, TCP, UDP, Chat, File Transfer."""
import logging
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QTabWidget, QTextEdit, QHeaderView, QComboBox,
    QSpinBox, QAbstractItemView, QFileDialog, QProgressBar,
    QScrollArea, QSplitter
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QBrush

from services.connection_service import ConnectionService
from services.monitoring_service import MonitoringService
from network.socket_manager import (
    TCPServer, TCPClient, UDPManager,
    FileTransferServer, FileTransferClient,
    LANChatServer, LANChatClient
)
from network.network_utils import get_local_ip
from utils.validators import validate_ip, validate_port
from utils.helpers import format_bytes, format_speed, get_timestamp

logger = logging.getLogger(__name__)


class ConnectionsPage(QWidget):
    """Connections management page with multiple tabs."""

    show_toast = Signal(str, str)

    def __init__(self, connection_service: ConnectionService,
                 monitoring_service: MonitoringService, parent=None):
        super().__init__(parent)
        self._conn_service = connection_service
        self._mon_service = monitoring_service

        # Network components
        self._tcp_server = TCPServer()
        self._tcp_client = TCPClient()
        self._udp_manager = UDPManager()
        self._file_server = FileTransferServer()
        self._file_client = FileTransferClient()
        self._chat_server = LANChatServer()
        self._chat_client = LANChatClient()

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Build connections page with tabs."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Connections")
        title.setObjectName("page_title")
        layout.addWidget(title)

        subtitle = QLabel("tcp.monitor | udp.monitor | chat | file.transfer")
        subtitle.setObjectName("page_subtitle")
        layout.addWidget(subtitle)

        # Tab widget
        tabs = QTabWidget()
        tabs.addTab(self._create_active_tab(), "📡 Active")
        tabs.addTab(self._create_tcp_server_tab(), "🖥️ TCP Server")
        tabs.addTab(self._create_tcp_client_tab(), "💻 TCP Client")
        tabs.addTab(self._create_udp_tab(), "📡 UDP")
        tabs.addTab(self._create_chat_tab(), "💬 Chat")
        tabs.addTab(self._create_file_tab(), "📁 File Transfer")
        layout.addWidget(tabs, 1)

    # ─── Tab 1: Active Connections ───────────────────────────────

    def _create_active_tab(self) -> QWidget:
        """Create active connections tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)

        # Controls
        controls = QHBoxLayout()

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._refresh_active)
        controls.addWidget(refresh_btn)

        self._conn_filter = QComboBox()
        self._conn_filter.addItems(["All", "TCP", "UDP"])
        self._conn_filter.currentIndexChanged.connect(self._refresh_active)
        controls.addWidget(self._conn_filter)

        self._conn_search = QLineEdit()
        self._conn_search.setPlaceholderText("🔍 Search...")
        self._conn_search.textChanged.connect(self._filter_connections)
        controls.addWidget(self._conn_search)

        controls.addStretch()
        layout.addLayout(controls)

        # Table
        self._conn_table = QTableWidget()
        self._conn_table.setAlternatingRowColors(True)
        self._conn_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._conn_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._conn_table.setSortingEnabled(True)
        self._conn_table.setColumnCount(8)
        self._conn_table.setHorizontalHeaderLabels([
            "Local Address", "Local Port", "Remote Address", "Remote Port",
            "Protocol", "State", "PID", "Process"
        ])

        header = self._conn_table.horizontalHeader()
        for i in range(8):
            header.setSectionResizeMode(
                i, QHeaderView.Stretch if i in (0, 2, 7) else QHeaderView.ResizeToContents
            )

        layout.addWidget(self._conn_table, 1)
        return widget

    # ─── Tab 2: TCP Server ───────────────────────────────────────

    def _create_tcp_server_tab(self) -> QWidget:
        """Create TCP server tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)

        # Server config
        config_row = QHBoxLayout()
        config_row.addWidget(QLabel("Port:"))
        self._server_port = QSpinBox()
        self._server_port.setButtonSymbols(QSpinBox.NoButtons)
        self._server_port.setRange(1, 65535)
        self._server_port.setValue(5000)
        config_row.addWidget(self._server_port)

        self._server_status = QLabel("⬛ Stopped")
        config_row.addWidget(self._server_status)
        config_row.addStretch()

        self._start_server_btn = QPushButton("▶️ Start Server")
        self._start_server_btn.clicked.connect(self._toggle_tcp_server)
        config_row.addWidget(self._start_server_btn)

        layout.addLayout(config_row)

        # Splitter for clients and messages
        splitter = QSplitter(Qt.Horizontal)

        # Client list
        client_panel = QFrame()
        client_panel.setObjectName("card")
        cl = QVBoxLayout(client_panel)
        cl.addWidget(QLabel("Connected Clients"))
        self._client_list = QTableWidget()
        self._client_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._client_list.setColumnCount(1)
        self._client_list.setHorizontalHeaderLabels(["Address"])
        self._client_list.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        cl.addWidget(self._client_list)
        splitter.addWidget(client_panel)

        # Server message log
        msg_panel = QFrame()
        msg_panel.setObjectName("card")
        ml = QVBoxLayout(msg_panel)
        ml.addWidget(QLabel("Server Messages"))
        self._server_log = QTextEdit()
        self._server_log.setReadOnly(True)
        ml.addWidget(self._server_log)

        # Send to all clients
        send_row = QHBoxLayout()
        self._server_msg_input = QLineEdit()
        self._server_msg_input.setPlaceholderText("Send message to all clients...")
        self._server_msg_input.returnPressed.connect(self._server_broadcast)
        send_row.addWidget(self._server_msg_input)
        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self._server_broadcast)
        send_row.addWidget(send_btn)
        ml.addLayout(send_row)

        splitter.addWidget(msg_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter, 1)
        return widget

    # ─── Tab 3: TCP Client ───────────────────────────────────────

    def _create_tcp_client_tab(self) -> QWidget:
        """Create TCP client tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)

        # Connection
        conn_row = QHBoxLayout()
        conn_row.addWidget(QLabel("Server IP:"))
        self._client_ip = QLineEdit()
        self._client_ip.setPlaceholderText("192.168.1.x")
        conn_row.addWidget(self._client_ip)

        conn_row.addWidget(QLabel("Port:"))
        self._client_port = QSpinBox()
        self._client_port.setButtonSymbols(QSpinBox.NoButtons)
        self._client_port.setRange(1, 65535)
        self._client_port.setValue(5000)
        conn_row.addWidget(self._client_port)

        self._client_status = QLabel("⬛ Disconnected")
        conn_row.addWidget(self._client_status)

        self._connect_btn = QPushButton("🔗 Connect")
        self._connect_btn.clicked.connect(self._toggle_tcp_client)
        conn_row.addWidget(self._connect_btn)

        layout.addLayout(conn_row)

        # Messages
        self._client_log = QTextEdit()
        self._client_log.setReadOnly(True)
        layout.addWidget(self._client_log, 1)

        # Send
        send_row = QHBoxLayout()
        self._client_msg_input = QLineEdit()
        self._client_msg_input.setPlaceholderText("Type a message...")
        self._client_msg_input.returnPressed.connect(self._client_send)
        self._client_msg_input.setEnabled(False)
        send_row.addWidget(self._client_msg_input)

        self._client_send_btn = QPushButton("Send")
        self._client_send_btn.clicked.connect(self._client_send)
        self._client_send_btn.setEnabled(False)
        send_row.addWidget(self._client_send_btn)

        layout.addLayout(send_row)
        return widget

    # ─── Tab 4: UDP ──────────────────────────────────────────────

    def _create_udp_tab(self) -> QWidget:
        """Create UDP tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)

        # Listener
        listener_row = QHBoxLayout()
        listener_row.addWidget(QLabel("Listen Port:"))
        self._udp_port = QSpinBox()
        self._udp_port.setButtonSymbols(QSpinBox.NoButtons)
        self._udp_port.setRange(1, 65535)
        self._udp_port.setValue(5001)
        listener_row.addWidget(self._udp_port)

        self._udp_status = QLabel("⬛ Stopped")
        listener_row.addWidget(self._udp_status)

        self._udp_listen_btn = QPushButton("▶️ Start Listener")
        self._udp_listen_btn.clicked.connect(self._toggle_udp)
        listener_row.addWidget(self._udp_listen_btn)

        listener_row.addStretch()
        layout.addLayout(listener_row)

        # UDP Log
        self._udp_log = QTextEdit()
        self._udp_log.setReadOnly(True)
        layout.addWidget(self._udp_log, 1)

        # Send
        send_frame = QFrame()
        send_frame.setObjectName("card")
        sl = QVBoxLayout(send_frame)
        sl.addWidget(QLabel("Send UDP Message"))

        target_row = QHBoxLayout()
        target_row.addWidget(QLabel("Target IP:"))
        self._udp_target_ip = QLineEdit()
        self._udp_target_ip.setPlaceholderText("192.168.1.x")
        target_row.addWidget(self._udp_target_ip)

        target_row.addWidget(QLabel("Port:"))
        self._udp_target_port = QSpinBox()
        self._udp_target_port.setButtonSymbols(QSpinBox.NoButtons)
        self._udp_target_port.setRange(1, 65535)
        self._udp_target_port.setValue(5001)
        target_row.addWidget(self._udp_target_port)
        sl.addLayout(target_row)

        msg_row = QHBoxLayout()
        self._udp_msg_input = QLineEdit()
        self._udp_msg_input.setPlaceholderText("Message...")
        self._udp_msg_input.returnPressed.connect(self._udp_send)
        msg_row.addWidget(self._udp_msg_input)
        udp_send_btn = QPushButton("Send")
        udp_send_btn.clicked.connect(self._udp_send)
        msg_row.addWidget(udp_send_btn)
        sl.addLayout(msg_row)

        layout.addWidget(send_frame)
        return widget

    # ─── Tab 5: LAN Chat ────────────────────────────────────────

    def _create_chat_tab(self) -> QWidget:
        """Create LAN chat tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)

        # Chat config
        config_row = QHBoxLayout()
        config_row.addWidget(QLabel("Username:"))
        self._chat_username = QLineEdit()
        self._chat_username.setPlaceholderText("Your name")
        self._chat_username.setMaximumWidth(150)
        config_row.addWidget(self._chat_username)

        config_row.addWidget(QLabel("Port:"))
        self._chat_port = QSpinBox()
        self._chat_port.setButtonSymbols(QSpinBox.NoButtons)
        self._chat_port.setRange(1, 65535)
        self._chat_port.setValue(5002)
        config_row.addWidget(self._chat_port)

        self._chat_server_btn = QPushButton("▶️ Host Chat")
        self._chat_server_btn.clicked.connect(self._toggle_chat_server)
        config_row.addWidget(self._chat_server_btn)

        config_row.addWidget(QLabel("  |  Server IP:"))
        self._chat_server_ip = QLineEdit()
        self._chat_server_ip.setPlaceholderText("192.168.1.x")
        self._chat_server_ip.setMaximumWidth(150)
        config_row.addWidget(self._chat_server_ip)

        self._chat_connect_btn = QPushButton("🔗 Join Chat")
        self._chat_connect_btn.clicked.connect(self._toggle_chat_client)
        config_row.addWidget(self._chat_connect_btn)

        self._chat_status = QLabel("")
        config_row.addWidget(self._chat_status)
        config_row.addStretch()
        layout.addLayout(config_row)

        # Chat messages area
        self._chat_display = QTextEdit()
        self._chat_display.setReadOnly(True)
        layout.addWidget(self._chat_display, 1)

        # Chat input
        input_row = QHBoxLayout()
        self._chat_input = QLineEdit()
        self._chat_input.setPlaceholderText("Type a message...")
        self._chat_input.returnPressed.connect(self._send_chat)
        self._chat_input.setEnabled(False)
        input_row.addWidget(self._chat_input)

        self._chat_send_btn = QPushButton("Send")
        self._chat_send_btn.clicked.connect(self._send_chat)
        self._chat_send_btn.setEnabled(False)
        input_row.addWidget(self._chat_send_btn)
        layout.addLayout(input_row)

        return widget

    # ─── Tab 6: File Transfer ────────────────────────────────────

    def _create_file_tab(self) -> QWidget:
        """Create file transfer tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)

        # Receive section
        recv_frame = QFrame()
        recv_frame.setObjectName("card")
        rl = QVBoxLayout(recv_frame)
        rl.addWidget(QLabel("📥 Receive Files"))

        recv_row = QHBoxLayout()
        recv_row.addWidget(QLabel("Port:"))
        self._file_recv_port = QSpinBox()
        self._file_recv_port.setButtonSymbols(QSpinBox.NoButtons)
        self._file_recv_port.setRange(1, 65535)
        self._file_recv_port.setValue(5003)
        recv_row.addWidget(self._file_recv_port)

        self._file_recv_status = QLabel("⬛ Not listening")
        recv_row.addWidget(self._file_recv_status)

        self._file_recv_btn = QPushButton("▶️ Start Receiving")
        self._file_recv_btn.clicked.connect(self._toggle_file_server)
        recv_row.addWidget(self._file_recv_btn)
        recv_row.addStretch()
        rl.addLayout(recv_row)

        self._file_recv_progress = QProgressBar()
        self._file_recv_progress.setVisible(False)
        rl.addWidget(self._file_recv_progress)

        layout.addWidget(recv_frame)

        # Send section
        send_frame = QFrame()
        send_frame.setObjectName("card")
        sl = QVBoxLayout(send_frame)
        sl.addWidget(QLabel("📤 Send File"))

        target_row = QHBoxLayout()
        target_row.addWidget(QLabel("Target IP:"))
        self._file_target_ip = QLineEdit()
        self._file_target_ip.setPlaceholderText("192.168.1.x")
        target_row.addWidget(self._file_target_ip)

        target_row.addWidget(QLabel("Port:"))
        self._file_target_port = QSpinBox()
        self._file_target_port.setButtonSymbols(QSpinBox.NoButtons)
        self._file_target_port.setRange(1, 65535)
        self._file_target_port.setValue(5003)
        target_row.addWidget(self._file_target_port)
        sl.addLayout(target_row)

        file_row = QHBoxLayout()
        self._file_path_input = QLineEdit()
        self._file_path_input.setPlaceholderText("Select a file...")
        self._file_path_input.setReadOnly(True)
        file_row.addWidget(self._file_path_input)

        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("secondary_button")
        browse_btn.clicked.connect(self._browse_file)
        file_row.addWidget(browse_btn)

        self._file_send_btn = QPushButton("📤 Send")
        self._file_send_btn.clicked.connect(self._send_file)
        file_row.addWidget(self._file_send_btn)
        sl.addLayout(file_row)

        self._file_send_progress = QProgressBar()
        self._file_send_progress.setVisible(False)
        sl.addWidget(self._file_send_progress)

        self._file_speed_label = QLabel("")
        sl.addWidget(self._file_speed_label)

        layout.addWidget(send_frame)

        # Transfer log
        self._file_log = QTextEdit()
        self._file_log.setReadOnly(True)
        layout.addWidget(self._file_log, 1)

        return widget

    # ─── Signal Connections ──────────────────────────────────────

    def _connect_signals(self) -> None:
        """Connect all network component signals."""
        # TCP Server
        self._tcp_server.server_started.connect(self._on_server_started)
        self._tcp_server.server_stopped.connect(self._on_server_stopped)
        self._tcp_server.server_error.connect(self._on_server_error)
        self._tcp_server.client_connected.connect(self._on_client_connected)
        self._tcp_server.client_disconnected.connect(self._on_client_disconnected)
        self._tcp_server.message_received.connect(self._on_server_message)

        # TCP Client
        self._tcp_client.connected.connect(self._on_client_connected_to_server)
        self._tcp_client.disconnected.connect(self._on_client_disconnected_from_server)
        self._tcp_client.message_received.connect(self._on_client_message)
        self._tcp_client.connection_error.connect(self._on_client_error)

        # UDP
        self._udp_manager.listener_started.connect(self._on_udp_started)
        self._udp_manager.listener_stopped.connect(self._on_udp_stopped)
        self._udp_manager.message_received.connect(self._on_udp_received)
        self._udp_manager.udp_error.connect(self._on_udp_error)

        # File Transfer
        self._file_server.server_ready.connect(self._on_file_server_ready)
        self._file_server.server_stopped.connect(self._on_file_server_stopped)
        self._file_server.transfer_started.connect(self._on_file_recv_started)
        self._file_server.transfer_progress.connect(self._on_file_recv_progress)
        self._file_server.transfer_complete.connect(self._on_file_recv_complete)
        self._file_server.transfer_error.connect(self._on_file_error)

        self._file_client.transfer_started.connect(self._on_file_send_started)
        self._file_client.transfer_progress.connect(self._on_file_send_progress)
        self._file_client.transfer_complete.connect(self._on_file_send_complete)
        self._file_client.transfer_error.connect(self._on_file_error)
        self._file_client.speed_update.connect(self._on_file_speed)

        # Chat
        self._chat_server.server_started.connect(self._on_chat_server_started)
        self._chat_server.server_stopped.connect(self._on_chat_server_stopped)
        self._chat_server.chat_message.connect(self._on_chat_message_server)
        self._chat_server.user_joined.connect(self._on_chat_user_joined)
        self._chat_server.user_left.connect(self._on_chat_user_left)
        self._chat_server.chat_error.connect(self._on_chat_error)

        self._chat_client.connected.connect(self._on_chat_client_connected)
        self._chat_client.disconnected.connect(self._on_chat_client_disconnected)
        self._chat_client.chat_message.connect(self._on_chat_message_client)
        self._chat_client.chat_error.connect(self._on_chat_error)

    # ─── Active Connections Logic ────────────────────────────────

    def _refresh_active(self) -> None:
        """Refresh active connections table with color coding."""
        proto_filter = self._conn_filter.currentText()
        proto = None if proto_filter == "All" else proto_filter
        connections = self._mon_service.get_active_connections(proto)

        self._conn_table.setSortingEnabled(False)
        self._conn_table.setRowCount(0)

        # Connection state colors
        state_colors = {
            "ESTABLISHED": "#00ff88",
            "LISTEN":      "#00d4ff",
            "TIME_WAIT":   "#ff8c00",
            "CLOSE_WAIT":  "#ff8c00",
            "SYN_SENT":    "#ffdd44",
            "SYN_RECEIVED": "#ffdd44",
            "FIN_WAIT_1":  "#ff6633",
            "FIN_WAIT_2":  "#ff6633",
            "LAST_ACK":    "#ff3333",
            "CLOSED":      "#5a7a9a",
            "NONE":        "#3a5a7a",
        }

        mono_font = QFont()
        mono_font.setFamilies(["JetBrains Mono", "Cascadia Code", "Consolas"])
        mono_font.setPointSize(11)

        for conn in connections:
            row = self._conn_table.rowCount()
            self._conn_table.insertRow(row)

            # Local Address (monospace + cyan)
            local_addr_item = QTableWidgetItem(conn.local_address)
            local_addr_item.setFont(mono_font)
            local_addr_item.setForeground(QBrush(QColor("#00d4ff")))
            self._conn_table.setItem(row, 0, local_addr_item)

            # Local Port (monospace + purple)
            local_port_item = QTableWidgetItem(str(conn.local_port))
            local_port_item.setFont(mono_font)
            local_port_item.setForeground(QBrush(QColor("#b8a0ff")))
            self._conn_table.setItem(row, 1, local_port_item)

            # Remote Address (monospace + muted)
            remote_addr_item = QTableWidgetItem(conn.remote_address)
            remote_addr_item.setFont(mono_font)
            remote_addr_item.setForeground(QBrush(QColor("#7a9cbf")))
            self._conn_table.setItem(row, 2, remote_addr_item)

            # Remote Port
            remote_port_item = QTableWidgetItem(str(conn.remote_port))
            remote_port_item.setFont(mono_font)
            remote_port_item.setForeground(QBrush(QColor("#b8a0ff")))
            self._conn_table.setItem(row, 3, remote_port_item)

            # Protocol
            proto_item = QTableWidgetItem(conn.protocol)
            proto_item.setForeground(QBrush(QColor("#00d4ff")))
            self._conn_table.setItem(row, 4, proto_item)

            # State (color coded)
            state = conn.state
            state_item = QTableWidgetItem(state)
            state_color = state_colors.get(state.upper(), "#5a7a9a")
            state_item.setForeground(QBrush(QColor(state_color)))
            state_item.setFont(mono_font)
            self._conn_table.setItem(row, 5, state_item)

            # PID
            pid_item = QTableWidgetItem(
                str(conn.pid) if conn.pid else "N/A"
            )
            pid_item.setForeground(QBrush(QColor("#5a7a9a")))
            pid_item.setFont(mono_font)
            self._conn_table.setItem(row, 6, pid_item)

            # Process name
            self._conn_table.setItem(row, 7, QTableWidgetItem(conn.process_name))

        self._conn_table.setSortingEnabled(True)

    def _filter_connections(self) -> None:
        """Filter connections table by search text."""
        search = self._conn_search.text().lower()
        for row in range(self._conn_table.rowCount()):
            match = False
            for col in range(self._conn_table.columnCount()):
                item = self._conn_table.item(row, col)
                if item and search in item.text().lower():
                    match = True
                    break
            self._conn_table.setRowHidden(row, not match if search else False)

    # ─── TCP Server Logic ────────────────────────────────────────

    def _toggle_tcp_server(self) -> None:
        if self._tcp_server.is_running:
            self._tcp_server.stop()
        else:
            port = self._server_port.value()
            self._tcp_server.configure(port=port)
            self._tcp_server.start()

    def _on_server_started(self, port: int) -> None:
        self._server_status.setText(f"🟢 Running on port {port}")
        self._start_server_btn.setText("⬛ Stop Server")
        self._start_server_btn.setObjectName("danger_button")
        self._start_server_btn.style().unpolish(self._start_server_btn)
        self._start_server_btn.style().polish(self._start_server_btn)
        self._server_log.append(f"[{get_timestamp()}] Server started on port {port}")
        local_ip = get_local_ip()
        self._server_log.append(f"[{get_timestamp()}] Listening at {local_ip}:{port}")

    def _on_server_stopped(self) -> None:
        self._server_status.setText("⬛ Stopped")
        self._start_server_btn.setText("▶️ Start Server")
        self._start_server_btn.setObjectName("")
        self._start_server_btn.style().unpolish(self._start_server_btn)
        self._start_server_btn.style().polish(self._start_server_btn)
        self._client_list.setRowCount(0)
        self._server_log.append(f"[{get_timestamp()}] Server stopped")

    def _on_server_error(self, error: str) -> None:
        self._server_status.setText("🔴 Error")
        self._server_log.append(f"[{get_timestamp()}] ERROR: {error}")
        self.show_toast.emit(error, "error")

    def _on_client_connected(self, addr: str) -> None:
        row = self._client_list.rowCount()
        self._client_list.insertRow(row)
        self._client_list.setItem(row, 0, QTableWidgetItem(addr))
        self._server_log.append(f"[{get_timestamp()}] Client connected: {addr}")

    def _on_client_disconnected(self, addr: str) -> None:
        for row in range(self._client_list.rowCount()):
            item = self._client_list.item(row, 0)
            if item and item.text() == addr:
                self._client_list.removeRow(row)
                break
        self._server_log.append(f"[{get_timestamp()}] Client disconnected: {addr}")

    def _on_server_message(self, addr: str, msg: str) -> None:
        self._server_log.append(f"[{get_timestamp()}] {addr}: {msg}")

    def _server_broadcast(self) -> None:
        msg = self._server_msg_input.text().strip()
        if msg and self._tcp_server.is_running:
            self._tcp_server.broadcast(msg)
            self._server_log.append(f"[{get_timestamp()}] Server: {msg}")
            self._server_msg_input.clear()

    # ─── TCP Client Logic ────────────────────────────────────────

    def _toggle_tcp_client(self) -> None:
        if self._tcp_client.is_connected:
            self._tcp_client.disconnect_from_server()
        else:
            ip = self._client_ip.text().strip()
            port = self._client_port.value()
            if not validate_ip(ip):
                self.show_toast.emit("Invalid IP address", "error")
                return
            # Wait for previous thread to finish if still running
            if self._tcp_client.isRunning():
                self._tcp_client.wait(2000)
            self._tcp_client.configure(ip, port)
            self._tcp_client.start()

    def _on_client_connected_to_server(self, addr: str) -> None:
        self._client_status.setText(f"🟢 Connected to {addr}")
        self._connect_btn.setText("🔌 Disconnect")
        self._connect_btn.setObjectName("danger_button")
        self._connect_btn.style().unpolish(self._connect_btn)
        self._connect_btn.style().polish(self._connect_btn)
        self._client_msg_input.setEnabled(True)
        self._client_send_btn.setEnabled(True)
        self._client_log.append(f"[{get_timestamp()}] Connected to {addr}")

    def _on_client_disconnected_from_server(self) -> None:
        self._client_status.setText("⬛ Disconnected")
        self._connect_btn.setText("🔗 Connect")
        self._connect_btn.setObjectName("")
        self._connect_btn.style().unpolish(self._connect_btn)
        self._connect_btn.style().polish(self._connect_btn)
        self._client_msg_input.setEnabled(False)
        self._client_send_btn.setEnabled(False)
        self._client_log.append(f"[{get_timestamp()}] Disconnected")

    def _on_client_message(self, msg: str) -> None:
        self._client_log.append(f"[{get_timestamp()}] Server: {msg}")

    def _on_client_error(self, error: str) -> None:
        self._client_log.append(f"[{get_timestamp()}] ERROR: {error}")
        self.show_toast.emit(error, "error")

    def _client_send(self) -> None:
        msg = self._client_msg_input.text().strip()
        if msg and self._tcp_client.is_connected:
            if self._tcp_client.send_message(msg):
                self._client_log.append(f"[{get_timestamp()}] You: {msg}")
                self._client_msg_input.clear()

    # ─── UDP Logic ───────────────────────────────────────────────

    def _toggle_udp(self) -> None:
        if self._udp_manager.is_running:
            self._udp_manager.stop()
        else:
            port = self._udp_port.value()
            self._udp_manager.configure(port=port)
            self._udp_manager.start()

    def _on_udp_started(self, port: int) -> None:
        self._udp_status.setText(f"🟢 Listening on port {port}")
        self._udp_listen_btn.setText("⬛ Stop")
        self._udp_listen_btn.setObjectName("danger_button")
        self._udp_listen_btn.style().unpolish(self._udp_listen_btn)
        self._udp_listen_btn.style().polish(self._udp_listen_btn)
        self._udp_log.append(f"[{get_timestamp()}] UDP listener started on port {port}")

    def _on_udp_stopped(self) -> None:
        self._udp_status.setText("⬛ Stopped")
        self._udp_listen_btn.setText("▶️ Start Listener")
        self._udp_listen_btn.setObjectName("")
        self._udp_listen_btn.style().unpolish(self._udp_listen_btn)
        self._udp_listen_btn.style().polish(self._udp_listen_btn)
        self._udp_log.append(f"[{get_timestamp()}] UDP listener stopped")

    def _on_udp_received(self, sender: str, msg: str) -> None:
        self._udp_log.append(f"[{get_timestamp()}] From {sender}: {msg}")

    def _on_udp_error(self, error: str) -> None:
        self._udp_log.append(f"[{get_timestamp()}] ERROR: {error}")
        self.show_toast.emit(error, "error")

    def _udp_send(self) -> None:
        ip = self._udp_target_ip.text().strip()
        port = self._udp_target_port.value()
        msg = self._udp_msg_input.text().strip()

        if not validate_ip(ip):
            self.show_toast.emit("Invalid target IP", "error")
            return
        if not msg:
            return

        if self._udp_manager.send_message(ip, port, msg):
            self._udp_log.append(f"[{get_timestamp()}] To {ip}:{port}: {msg}")
            self._udp_msg_input.clear()

    # ─── Chat Logic ──────────────────────────────────────────────

    def _toggle_chat_server(self) -> None:
        if self._chat_server.isRunning():
            self._chat_server.stop()
        else:
            port = self._chat_port.value()
            self._chat_server.configure(port=port)
            self._chat_server.start()

    def _toggle_chat_client(self) -> None:
        if self._chat_client.is_connected:
            self._chat_client.disconnect_chat()
        else:
            ip = self._chat_server_ip.text().strip()
            port = self._chat_port.value()
            username = self._chat_username.text().strip() or "User"
            if not validate_ip(ip):
                self.show_toast.emit("Invalid server IP", "error")
                return
            # Wait for previous thread to finish if still running
            if self._chat_client.isRunning():
                self._chat_client.wait(2000)
            self._chat_client.configure(ip, port, username)
            self._chat_client.start()

    def _on_chat_server_started(self, port: int) -> None:
        local_ip = get_local_ip()
        self._chat_status.setText(f"🟢 Hosting on {local_ip}:{port}")
        self._chat_server_btn.setText("⬛ Stop Host")
        self._chat_input.setEnabled(True)
        self._chat_send_btn.setEnabled(True)
        self._chat_display.append(
            f"<b style='color:#3fb950'>System:</b> Chat server started. "
            f"Others can connect to {local_ip}:{port}"
        )

    def _on_chat_server_stopped(self) -> None:
        self._chat_status.setText("")
        self._chat_server_btn.setText("▶️ Host Chat")
        self._chat_input.setEnabled(False)
        self._chat_send_btn.setEnabled(False)

    def _on_chat_user_joined(self, username: str, ip: str) -> None:
        self._chat_display.append(
            f"<b style='color:#58a6ff'>{username}</b> ({ip}) has joined"
        )

    def _on_chat_user_left(self, username: str, ip: str) -> None:
        self._chat_display.append(
            f"<b style='color:#8b949e'>{username}</b> ({ip}) has left"
        )

    def _on_chat_message_server(self, username: str, msg: str,
                                 ip: str, timestamp: str) -> None:
        self._chat_display.append(
            f"<b style='color:#58a6ff'>[{timestamp}] {username}:</b> {msg}"
        )

    def _on_chat_client_connected(self) -> None:
        self._chat_status.setText("🟢 Connected")
        self._chat_connect_btn.setText("🔌 Leave")
        self._chat_input.setEnabled(True)
        self._chat_send_btn.setEnabled(True)
        self._chat_display.append(
            "<b style='color:#3fb950'>System:</b> Connected to chat!"
        )

    def _on_chat_client_disconnected(self) -> None:
        self._chat_status.setText("")
        self._chat_connect_btn.setText("🔗 Join Chat")
        self._chat_input.setEnabled(False)
        self._chat_send_btn.setEnabled(False)
        self._chat_display.append(
            "<b style='color:#8b949e'>System:</b> Disconnected from chat"
        )

    def _on_chat_message_client(self, username: str, msg: str,
                                 timestamp: str) -> None:
        self._chat_display.append(
            f"<b style='color:#58a6ff'>[{timestamp}] {username}:</b> {msg}"
        )

    def _on_chat_error(self, error: str) -> None:
        self._chat_display.append(
            f"<b style='color:#f85149'>Error:</b> {error}"
        )

    def _send_chat(self) -> None:
        msg = self._chat_input.text().strip()
        if not msg:
            return

        username = self._chat_username.text().strip() or "User"

        # If hosting, broadcast
        if self._chat_server.isRunning():
            self._chat_server.broadcast_message(username, msg)
            self._chat_display.append(
                f"<b style='color:#3fb950'>[{get_timestamp().split(' ')[1]}] "
                f"{username} (You):</b> {msg}"
            )
            self._chat_input.clear()
        # If client, send
        elif self._chat_client.is_connected:
            if self._chat_client.send_chat_message(msg):
                self._chat_display.append(
                    f"<b style='color:#3fb950'>[{get_timestamp().split(' ')[1]}] "
                    f"{username} (You):</b> {msg}"
                )
                self._chat_input.clear()

    # ─── File Transfer Logic ─────────────────────────────────────

    def _toggle_file_server(self) -> None:
        if self._file_server.isRunning():
            self._file_server.stop()
        else:
            port = self._file_recv_port.value()
            self._file_server.configure(port=port)
            self._file_server.start()

    def _on_file_server_ready(self, port: int) -> None:
        local_ip = get_local_ip()
        self._file_recv_status.setText(f"🟢 Listening on {local_ip}:{port}")
        self._file_recv_btn.setText("⬛ Stop")
        self._file_log.append(f"[{get_timestamp()}] File receiver ready on port {port}")

    def _on_file_server_stopped(self) -> None:
        self._file_recv_status.setText("⬛ Not listening")
        self._file_recv_btn.setText("▶️ Start Receiving")
        self._file_recv_progress.setVisible(False)

    def _on_file_recv_started(self, filename: str, size: int, sender: str) -> None:
        self._file_recv_progress.setVisible(True)
        self._file_recv_progress.setMaximum(size)
        self._file_recv_progress.setValue(0)
        self._file_log.append(
            f"[{get_timestamp()}] Receiving: {filename} "
            f"({format_bytes(size)}) from {sender}"
        )

    def _on_file_recv_progress(self, received: int, total: int) -> None:
        self._file_recv_progress.setMaximum(total)
        self._file_recv_progress.setValue(received)

    def _on_file_recv_complete(self, filename: str, path: str) -> None:
        self._file_recv_progress.setVisible(False)
        self._file_log.append(
            f"[{get_timestamp()}] ✅ File received: {filename} -> {path}"
        )
        self.show_toast.emit(f"File received: {filename}", "success")

    def _browse_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select File to Send")
        if path:
            self._file_path_input.setText(path)

    def _send_file(self) -> None:
        ip = self._file_target_ip.text().strip()
        port = self._file_target_port.value()
        path = self._file_path_input.text().strip()

        if not validate_ip(ip):
            self.show_toast.emit("Invalid target IP", "error")
            return
        if not path or not os.path.isfile(path):
            self.show_toast.emit("Please select a valid file", "error")
            return

        self._file_client.configure(ip, port, path)
        # Wait for previous transfer thread to finish if still running
        if self._file_client.isRunning():
            self._file_client.wait(2000)
        self._file_client.start()

    def _on_file_send_started(self, filename: str, size: int) -> None:
        self._file_send_progress.setVisible(True)
        self._file_send_progress.setMaximum(size)
        self._file_send_progress.setValue(0)
        self._file_log.append(
            f"[{get_timestamp()}] Sending: {filename} ({format_bytes(size)})"
        )

    def _on_file_send_progress(self, sent: int, total: int) -> None:
        self._file_send_progress.setMaximum(total)
        self._file_send_progress.setValue(sent)

    def _on_file_send_complete(self, filename: str) -> None:
        self._file_send_progress.setVisible(False)
        self._file_speed_label.setText("")
        self._file_log.append(
            f"[{get_timestamp()}] ✅ File sent: {filename}"
        )
        self.show_toast.emit(f"File sent: {filename}", "success")

    def _on_file_speed(self, speed: float) -> None:
        self._file_speed_label.setText(f"Speed: {format_speed(speed)}")

    def _on_file_error(self, error: str) -> None:
        self._file_send_progress.setVisible(False)
        self._file_recv_progress.setVisible(False)
        self._file_log.append(f"[{get_timestamp()}] ❌ {error}")
        self.show_toast.emit(error, "error")

    # ─── Refresh / Cleanup ───────────────────────────────────────

    def refresh(self) -> None:
        """Refresh active connections."""
        self._refresh_active()

    def cleanup(self) -> None:
        """Stop all network services."""
        if self._tcp_server.is_running:
            self._tcp_server.stop()
            self._tcp_server.wait(2000)

        if self._tcp_client.is_connected:
            self._tcp_client.disconnect_from_server()
            self._tcp_client.wait(2000)

        if self._udp_manager.is_running:
            self._udp_manager.stop()
            self._udp_manager.wait(2000)

        if self._file_server.isRunning():
            self._file_server.stop()
            self._file_server.wait(2000)

        if self._chat_server.isRunning():
            self._chat_server.stop()
            self._chat_server.wait(2000)

        if self._chat_client.is_connected:
            self._chat_client.disconnect_chat()
            self._chat_client.wait(2000)
