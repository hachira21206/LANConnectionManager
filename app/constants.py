"""Application constants including UI themes and enums."""
from enum import Enum, auto


class DeviceStatus(Enum):
    """Device connection status."""
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    UNKNOWN = "UNKNOWN"


class ConnectionState(Enum):
    """Connection state."""
    ESTABLISHED = "ESTABLISHED"
    LISTEN = "LISTEN"
    TIME_WAIT = "TIME_WAIT"
    CLOSE_WAIT = "CLOSE_WAIT"
    CLOSED = "CLOSED"
    SYN_SENT = "SYN_SENT"
    SYN_RECEIVED = "SYN_RECEIVED"
    FIN_WAIT_1 = "FIN_WAIT_1"
    FIN_WAIT_2 = "FIN_WAIT_2"
    LAST_ACK = "LAST_ACK"
    NONE = "NONE"


class Protocol(Enum):
    """Network protocol."""
    TCP = "TCP"
    UDP = "UDP"


class LogLevel(Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class TransferStatus(Enum):
    """File transfer status."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ServerStatus(Enum):
    """Server status."""
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    ERROR = "ERROR"


# Navigation items — using emoji for decoration
NAV_ITEMS = [
    ("dashboard", "🏠 Dashboard"),
    ("devices",   "💻 Devices"),
    ("connections","🔗 Connections"),
    ("monitor",   "📈 Monitor"),
    ("logs",      "📝 Logs"),
    ("settings",  "⚙️ Settings"),
]


# ——— Dark Theme (Cyber Dark — Sysadmin Edition) ————————————————————————
DARK_THEME = """
/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   CYBER DARK â€” Sysadmin / IT Professional Theme
   Color System:
     Deep BG:      #070b14
     Base BG:      #0c1220
     Surface:      #111827
     Elevated:     #1a2234
     Accent Cyan:  #00d4ff
     Online:       #00ff88
     Warning:      #ff8c00
     Error/Alert:  #ff3333
     Text Primary: #e2f0ff
     Text Muted:   #5a7a9a
     Border:       #1e3a5f
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */

QMainWindow, QWidget {
    background-color: #0c1220;
    color: #e2f0ff;
    font-family: 'Segoe UI Variable', 'Segoe UI', sans-serif;
    font-size: 14px;
}

QScrollArea { background-color: #0c1220; border: none; }
QScrollArea > QWidget > QWidget { background-color: #0c1220; }
QLabel { color: #e2f0ff; }

/* â”€â”€â”€ Sidebar â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
#sidebar {
    background-color: #070b14;
    border-right: 1px solid #1e3a5f;
    min-width: 240px;
    max-width: 240px;
}

#sidebar_logo_frame {
    background-color: transparent;
    border-bottom: 1px solid #1e3a5f;
    padding-bottom: 4px;
}

#sidebar_title {
    color: #00d4ff;
    font-size: 15px;
    font-weight: bold;
    padding: 20px 16px 4px 16px;
    letter-spacing: 1px;
}

#sidebar_subtitle {
    color: #5a7a9a;
    font-size: 10px;
    padding: 0px 16px 16px 16px;
    font-family: 'Cascadia Code', 'Consolas', monospace;
}

#sidebar_host_ip {
    color: #00d4ff;
    font-size: 11px;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    padding: 4px 16px 4px 16px;
    background-color: transparent;
}

#sidebar_host_label {
    color: #5a7a9a;
    font-size: 10px;
    padding: 10px 16px 0px 16px;
}

#sidebar_separator {
    background-color: #1e3a5f;
    max-height: 1px;
    min-height: 1px;
    margin: 8px 12px;
}

QPushButton#nav_button {
    background-color: transparent;
    color: #7a9cbf;
    text-align: left;
    padding: 11px 16px 11px 20px;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0px;
    margin: 1px 0px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton#nav_button:hover {
    background-color: #0f1e33;
    color: #ffffff;
    border-left: 3px solid #00d4ff88;
}

QPushButton#nav_button[active="true"] {
    background-color: #091929;
    color: #00d4ff;
    font-weight: bold;
    border-left: 3px solid #00d4ff;
}

/* â”€â”€â”€ Content Area â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
#content_area {
    background-color: #0c1220;
}

/* â”€â”€â”€ Page Headers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
#page_title {
    font-size: 20px;
    font-weight: bold;
    color: #e2f0ff;
    padding: 20px 24px 4px 24px;
    letter-spacing: 0.5px;
}

#page_subtitle {
    font-size: 12px;
    color: #5a7a9a;
    padding: 0px 24px 16px 24px;
    font-family: 'Cascadia Code', 'Consolas', monospace;
}

/* â”€â”€â”€ Cards â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
QFrame#card {
    background-color: #111827;
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 16px;
}

QFrame#card:hover {
    border-color: #00d4ff44;
}

QFrame#stat_card {
    background-color: #111827;
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 16px 20px;
}

QFrame#stat_card:hover {
    border-color: #00d4ff44;
    background-color: #141f32;
}

QFrame#alert_card {
    background-color: #1a1008;
    border: 1px solid #ff8c0055;
    border-left: 3px solid #ff8c00;
    border-radius: 8px;
    padding: 12px 16px;
}

QFrame#alert_card_error {
    background-color: #1a0808;
    border: 1px solid #ff333344;
    border-left: 3px solid #ff3333;
    border-radius: 8px;
    padding: 12px 16px;
}

/* â”€â”€â”€ Labels â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
QLabel#card_title {
    color: #5a7a9a;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1.5px;
}

QLabel#card_value {
    color: #e2f0ff;
    font-size: 28px;
    font-weight: bold;
    font-family: 'Cascadia Code', 'Consolas', monospace;
}

QLabel#card_value_small {
    color: #e2f0ff;
    font-size: 17px;
    font-weight: bold;
}

QLabel#card_icon {
    font-size: 22px;
}

QLabel#metric_value {
    color: #00d4ff;
    font-size: 24px;
    font-weight: bold;
    font-family: 'Cascadia Code', 'Consolas', monospace;
}

QLabel#metric_unit {
    color: #5a7a9a;
    font-size: 12px;
    font-family: 'Cascadia Code', 'Consolas', monospace;
}

/* Technical data labels (IP, MAC, Port) */
QLabel#ip_label {
    color: #00d4ff;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 13px;
}

QLabel#mac_label {
    color: #7a9cbf;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 12px;
}

QLabel#port_label {
    color: #b8a0ff;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 13px;
}

/* â”€â”€â”€ Status Badges â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
QLabel#status_online {
    color: #00ff88;
    font-weight: bold;
    font-size: 12px;
}

QLabel#status_offline {
    color: #ff3333;
    font-weight: bold;
    font-size: 12px;
}

QLabel#status_warning {
    color: #ff8c00;
    font-weight: bold;
    font-size: 12px;
}

QLabel#status_badge_online {
    color: #00ff88;
    background-color: #00ff8818;
    border: 1px solid #00ff8844;
    border-radius: 10px;
    padding: 2px 10px;
    font-weight: bold;
    font-size: 11px;
}

QLabel#status_badge_offline {
    color: #ff3333;
    background-color: #ff333318;
    border: 1px solid #ff333344;
    border-radius: 10px;
    padding: 2px 10px;
    font-weight: bold;
    font-size: 11px;
}

QLabel#status_badge_warn {
    color: #ff8c00;
    background-color: #ff8c0018;
    border: 1px solid #ff8c0044;
    border-radius: 10px;
    padding: 2px 10px;
    font-weight: bold;
    font-size: 11px;
}

/* Ping quality labels */
QLabel#ping_good { color: #00ff88; font-family: 'Cascadia Code', 'Consolas', monospace; font-weight: bold; }
QLabel#ping_warn { color: #ff8c00; font-family: 'Cascadia Code', 'Consolas', monospace; font-weight: bold; }
QLabel#ping_bad  { color: #ff3333; font-family: 'Cascadia Code', 'Consolas', monospace; font-weight: bold; }

/* â”€â”€â”€ Tables â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
QTableWidget {
    background-color: #0c1220;
    alternate-background-color: #0f1829;
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    gridline-color: #162035;
    color: #cce0ff;
    selection-background-color: #00d4ff22;
    selection-color: #e2f0ff;
    font-size: 12px;
}

QTableWidget::item {
    padding: 7px 10px;
    border-bottom: 1px solid #162035;
}

QTableWidget::item:selected {
    background-color: #00d4ff22;
    color: #e2f0ff;
    border-left: 2px solid #00d4ff;
}

QHeaderView::section {
    background-color: #0a1526;
    color: #5a7a9a;
    font-weight: bold;
    font-size: 11px;
    padding: 9px 10px;
    border: none;
    border-bottom: 1px solid #1e3a5f;
    border-right: 1px solid #162035;
    letter-spacing: 1px;
}

QHeaderView::section:first {
    border-top-left-radius: 8px;
}

/* â”€â”€â”€ Buttons â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
QPushButton {
    background-color: #005f7a;
    color: #e2f0ff;
    border: 1px solid #00d4ff44;
    border-radius: 7px;
    padding: 7px 18px;
    font-weight: bold;
    font-size: 12px;
    letter-spacing: 0.5px;
}

QPushButton:hover {
    background-color: #007a99;
    border-color: #00d4ffaa;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #004f66;
    border-color: #00d4ff;
}

QPushButton:disabled {
    background-color: #0f1829;
    color: #2a4a6a;
    border-color: #162035;
}

QPushButton#danger_button {
    background-color: #5c1515;
    border-color: #ff333344;
    color: #ffcccc;
}

QPushButton#danger_button:hover {
    background-color: #7a1c1c;
    border-color: #ff3333aa;
    color: #ffffff;
}

QPushButton#danger_button:pressed {
    background-color: #4a1010;
}

QPushButton#secondary_button {
    background-color: #0f1829;
    border: 1px solid #1e3a5f;
    color: #7a9cbf;
}

QPushButton#secondary_button:hover {
    background-color: #162035;
    border-color: #5a7a9a;
    color: #b8d4f0;
}

QPushButton#icon_button {
    background-color: transparent;
    border: none;
    padding: 5px;
    border-radius: 5px;
    color: #5a7a9a;
}

QPushButton#icon_button:hover {
    background-color: #162035;
    color: #00d4ff;
}

/* â”€â”€â”€ Input Fields â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
QLineEdit, QSpinBox, QComboBox {
    background-color: #0a1526;
    border: 1px solid #1e3a5f;
    border-radius: 7px;
    padding: 7px 12px;
    color: #cce0ff;
    font-size: 13px;
    selection-background-color: #00d4ff33;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border-color: #00d4ff;
    background-color: #0c1a2e;
    outline: none;
}

QLineEdit[readOnly="true"] {
    color: #5a7a9a;
    background-color: #080f1a;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox::down-arrow {
    image: url("ui/assets/down_arrow.svg");
    width: 14px;
    height: 14px;
}

QComboBox QAbstractItemView {
    background-color: #0f1829;
    border: 1px solid #1e3a5f;
    border-radius: 7px;
    color: #cce0ff;
    selection-background-color: #00d4ff22;
    selection-color: #e2f0ff;
    outline: none;
}

QSpinBox::up-button, QSpinBox::down-button {
    background-color: #1e3a5f;
    border: none;
    border-radius: 3px;
    width: 16px;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #00d4ff33;
}

/* â”€â”€â”€ Progress Bar â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
QProgressBar {
    background-color: #0a1526;
    border: 1px solid #1e3a5f;
    border-radius: 5px;
    height: 8px;
    text-align: center;
    color: transparent;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #00d4ff, stop:1 #00ff88);
    border-radius: 4px;
}

/* â”€â”€â”€ Scroll Bars â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
QScrollBar:vertical {
    background-color: #0c1220;
    width: 8px;
    border: none;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #1e3a5f;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #00d4ff44;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #0c1220;
    height: 8px;
    border: none;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #1e3a5f;
    border-radius: 4px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #00d4ff44;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* â”€â”€â”€ Tab Widget â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
QTabWidget::pane {
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    background-color: #0c1220;
    top: -1px;
}

QTabBar::tab {
    background-color: #0a1526;
    color: #5a7a9a;
    padding: 9px 18px;
    border: 1px solid #1e3a5f;
    border-bottom: none;
    border-top-left-radius: 7px;
    border-top-right-radius: 7px;
    margin-right: 2px;
    font-weight: 600;
    font-size: 12px;
}

QTabBar::tab:selected {
    background-color: #0c1220;
    color: #00d4ff;
    border-bottom: 2px solid #00d4ff;
}

QTabBar::tab:hover:!selected {
    color: #b8d4f0;
    background-color: #0f1829;
}

/* â”€â”€â”€ Text Areas (Terminal Style) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
QTextEdit, QPlainTextEdit {
    background-color: #070b14;
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    padding: 10px;
    color: #00ff88;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 12px;
    line-height: 1.5;
    selection-background-color: #00d4ff33;
}

QTextEdit#terminal_log {
    background-color: #040709;
    color: #7aff7a;
    border-color: #003300;
}

/* â”€â”€â”€ Group Box â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
QGroupBox {
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 20px;
    color: #5a7a9a;
    font-weight: bold;
    font-size: 12px;
    letter-spacing: 0.5px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 3px 12px;
    color: #e2f0ff;
    background-color: #0c1220;
}

/* â”€â”€â”€ Tooltips â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
QToolTip {
    background-color: #0f1829;
    color: #cce0ff;
    border: 1px solid #00d4ff44;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
    font-family: 'Cascadia Code', 'Consolas', monospace;
}

/* â”€â”€â”€ Status Bar â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
QStatusBar {
    background-color: #070b14;
    border-top: 1px solid #00d4ff22;
    color: #5a7a9a;
    font-size: 11px;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    padding: 3px 8px;
}

QStatusBar::item {
    border: none;
}

/* â”€â”€â”€ Splitter â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
QSplitter::handle {
    background-color: #1e3a5f;
    width: 1px;
}

QSplitter::handle:hover {
    background-color: #00d4ff44;
}

/* â”€â”€â”€ Chat Messages â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
QFrame#chat_message_sent {
    background-color: #004466;
    border: 1px solid #00d4ff44;
    border-radius: 10px;
    padding: 8px 14px;
}

QFrame#chat_message_received {
    background-color: #1a2234;
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 8px 14px;
}

QLabel#chat_username {
    color: #00d4ff;
    font-weight: bold;
    font-size: 11px;
    font-family: 'Cascadia Code', 'Consolas', monospace;
}

QLabel#chat_time {
    color: #2a4a6a;
    font-size: 10px;
    font-family: 'Cascadia Code', 'Consolas', monospace;
}

/* â”€â”€â”€ Toast Notifications â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
QFrame#toast {
    background-color: #0f1829;
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 12px 16px;
}

QFrame#toast_success {
    border-left: 4px solid #00ff88;
    background-color: #0a1e14;
}

QFrame#toast_error {
    border-left: 4px solid #ff3333;
    background-color: #1a0808;
}

QFrame#toast_warning {
    border-left: 4px solid #ff8c00;
    background-color: #1a1008;
}

QFrame#toast_info {
    border-left: 4px solid #00d4ff;
    background-color: #081626;
}

/* â”€â”€â”€ Log Level Colors â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
QLabel#log_debug   { color: #3a5a7a; }
QLabel#log_info    { color: #00d4ff; }
QLabel#log_warning { color: #ff8c00; }
QLabel#log_error   { color: #ff3333; font-weight: bold; }
"""

# ─── Light Theme (Professional Light) ────────────────────────────────
LIGHT_THEME = """
QMainWindow, QWidget {
    background-color: #f0f4f8;
    color: #1a2332;
    font-family: 'Segoe UI Variable', 'Segoe UI', sans-serif;
    font-size: 14px;
}

QScrollArea { background-color: #f0f4f8; border: none; }
QScrollArea > QWidget > QWidget { background-color: #f0f4f8; }
QLabel { color: #1a2332; }

#sidebar {
    background-color: #ffffff;
    border-right: 1px solid #c8d8e8;
    min-width: 240px;
    max-width: 240px;
}

#sidebar_logo_frame { background-color: transparent; border-bottom: 1px solid #c8d8e8; padding-bottom: 4px; }
#sidebar_title { color: #0969da; font-size: 15px; font-weight: bold; padding: 20px 16px 4px 16px; letter-spacing: 1px; }
#sidebar_subtitle { color: #5a7a9a; font-size: 10px; padding: 0px 16px 16px 16px; font-family: 'Cascadia Code', 'Consolas', monospace; }
#sidebar_host_ip { color: #0969da; font-size: 12px; font-weight: bold; font-family: 'Cascadia Code', 'Consolas', monospace; padding: 4px 16px; }
#sidebar_host_label { color: #5a7a9a; font-size: 10px; font-weight: bold; letter-spacing: 1px; padding: 10px 16px 0px 16px; }
#sidebar_separator { background-color: #e0ecf8; max-height: 1px; min-height: 1px; margin: 8px 12px; }

QPushButton#nav_button {
    background-color: transparent;
    color: #5a7a9a;
    text-align: left;
    padding: 11px 16px 11px 20px;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0px;
    margin: 1px 0px;
    font-size: 13px;
    font-weight: 500;
}
QPushButton#nav_button:hover { background-color: #f0f4f8; color: #0969da; border-left: 3px solid #79b8ff; }
QPushButton#nav_button[active="true"] { background-color: #e8f4ff; color: #0969da; font-weight: bold; border-left: 3px solid #0969da; }

#content_area { background-color: #f0f4f8; }
#page_title { font-size: 20px; font-weight: bold; color: #1a2332; padding: 20px 24px 4px 24px; }
#page_subtitle { font-size: 12px; color: #5a7a9a; padding: 0px 24px 16px 24px; font-family: 'Cascadia Code', 'Consolas', monospace; }

QFrame#card { background-color: #ffffff; border: 1px solid #c8d8e8; border-radius: 10px; padding: 16px; }
QFrame#card:hover { border-color: #0969da; }
QFrame#stat_card { background-color: #ffffff; border: 1px solid #c8d8e8; border-radius: 10px; padding: 16px 20px; }
QFrame#stat_card:hover { border-color: #0969da; }
QFrame#alert_card { background-color: #fff8f0; border: 1px solid #e8a030; border-left: 3px solid #e8a030; border-radius: 8px; padding: 12px 16px; }
QFrame#alert_card_error { background-color: #fff0f0; border: 1px solid #dc3030; border-left: 3px solid #dc3030; border-radius: 8px; padding: 12px 16px; }

QLabel#card_title { color: #5a7a9a; font-size: 11px; font-weight: bold; letter-spacing: 1.5px; }
QLabel#card_value { color: #1a2332; font-size: 28px; font-weight: bold; font-family: 'Cascadia Code', 'Consolas', monospace; }
QLabel#card_value_small { color: #1a2332; font-size: 17px; font-weight: bold; }
QLabel#card_icon { font-size: 22px; }
QLabel#metric_value { color: #0969da; font-size: 24px; font-weight: bold; font-family: 'Cascadia Code', 'Consolas', monospace; }
QLabel#ip_label { color: #0969da; font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 13px; }
QLabel#mac_label { color: #5a7a9a; font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 12px; }
QLabel#port_label { color: #7a50cc; font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 13px; }
QLabel#status_online { color: #1a7f37; font-weight: bold; font-size: 12px; }
QLabel#status_offline { color: #cf222e; font-weight: bold; font-size: 12px; }
QLabel#status_warning { color: #bf8700; font-weight: bold; font-size: 12px; }
QLabel#status_badge_online { color: #1a7f37; background-color: #dafbe1; border: 1px solid #1a7f3744; border-radius: 10px; padding: 2px 10px; font-weight: bold; font-size: 11px; }
QLabel#status_badge_offline { color: #cf222e; background-color: #ffe0e0; border: 1px solid #cf222e44; border-radius: 10px; padding: 2px 10px; font-weight: bold; font-size: 11px; }
QLabel#status_badge_warn { color: #bf8700; background-color: #fff8c5; border: 1px solid #bf870044; border-radius: 10px; padding: 2px 10px; font-weight: bold; font-size: 11px; }
QLabel#ping_good { color: #1a7f37; font-family: 'Cascadia Code', 'Consolas', monospace; font-weight: bold; }
QLabel#ping_warn { color: #bf8700; font-family: 'Cascadia Code', 'Consolas', monospace; font-weight: bold; }
QLabel#ping_bad  { color: #cf222e; font-family: 'Cascadia Code', 'Consolas', monospace; font-weight: bold; }

QTableWidget { background-color: #ffffff; alternate-background-color: #f8fbff; border: 1px solid #c8d8e8; border-radius: 8px; gridline-color: #e0ecf8; color: #1a2332; selection-background-color: #0969da22; selection-color: #1a2332; font-size: 12px; }
QTableWidget::item { padding: 7px 10px; border-bottom: 1px solid #e8f0f8; }
QTableWidget::item:selected { background-color: #0969da18; border-left: 2px solid #0969da; }
QHeaderView::section { background-color: #f0f4f8; color: #5a7a9a; font-weight: bold; font-size: 11px; padding: 9px 10px; border: none; border-bottom: 1px solid #c8d8e8; border-right: 1px solid #e0ecf8; letter-spacing: 1px; }

QPushButton { background-color: #0969da; color: #ffffff; border: none; border-radius: 7px; padding: 7px 18px; font-weight: bold; font-size: 12px; }
QPushButton:hover { background-color: #0860c8; }
QPushButton:pressed { background-color: #0550a0; }
QPushButton:disabled { background-color: #c8d8e8; color: #8aaccf; }
QPushButton#danger_button { background-color: #cf222e; }
QPushButton#danger_button:hover { background-color: #a40e26; }
QPushButton#secondary_button { background-color: #f0f4f8; border: 1px solid #c8d8e8; color: #1a2332; }
QPushButton#secondary_button:hover { background-color: #e0ecf8; border-color: #5a7a9a; }
QPushButton#icon_button { background-color: transparent; border: none; padding: 5px; border-radius: 5px; color: #5a7a9a; }
QPushButton#icon_button:hover { background-color: #e0ecf8; color: #0969da; }

QLineEdit, QSpinBox, QComboBox { background-color: #ffffff; border: 1px solid #c8d8e8; border-radius: 7px; padding: 7px 12px; color: #1a2332; font-size: 13px; }
QLineEdit:focus, QSpinBox:focus, QComboBox:focus { border-color: #0969da; }
QComboBox::drop-down { border: none; padding-right: 8px; }
QComboBox::down-arrow { image: url("ui/assets/down_arrow.svg"); width: 14px; height: 14px; }
QComboBox QAbstractItemView { background-color: #ffffff; border: 1px solid #c8d8e8; border-radius: 7px; color: #1a2332; selection-background-color: #0969da22; }

QProgressBar { background-color: #e0ecf8; border: none; border-radius: 5px; height: 8px; color: transparent; }
QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0969da, stop:1 #2da44e); border-radius: 4px; }

QScrollBar:vertical { background-color: #f0f4f8; width: 8px; border: none; }
QScrollBar::handle:vertical { background-color: #c8d8e8; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background-color: #5a7a9a; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar:horizontal { background-color: #f0f4f8; height: 8px; border: none; }
QScrollBar::handle:horizontal { background-color: #c8d8e8; border-radius: 4px; min-width: 30px; }
QScrollBar::handle:horizontal:hover { background-color: #5a7a9a; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }

QTabWidget::pane { border: 1px solid #c8d8e8; border-radius: 8px; background-color: #f0f4f8; top: -1px; }
QTabBar::tab { background-color: #e0ecf8; color: #5a7a9a; padding: 9px 18px; border: 1px solid #c8d8e8; border-bottom: none; border-top-left-radius: 7px; border-top-right-radius: 7px; margin-right: 2px; font-weight: 600; font-size: 12px; }
QTabBar::tab:selected { background-color: #f0f4f8; color: #0969da; border-bottom: 2px solid #0969da; }
QTabBar::tab:hover:!selected { color: #1a2332; background-color: #e8f4ff; }

QTextEdit, QPlainTextEdit { background-color: #ffffff; border: 1px solid #c8d8e8; border-radius: 8px; padding: 10px; color: #1a2332; font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 12px; }

QGroupBox { border: 1px solid #c8d8e8; border-radius: 8px; margin-top: 14px; padding-top: 20px; color: #5a7a9a; font-weight: bold; font-size: 12px; }
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 3px 12px; color: #0969da; background-color: #f0f4f8; }

QToolTip { background-color: #1a2332; color: #cce0ff; border: 1px solid #253447; border-radius: 6px; padding: 6px 10px; font-size: 12px; font-family: 'Cascadia Code', 'Consolas', monospace; }

QStatusBar { background-color: #1a2332; border-top: 1px solid #253447; color: #5a7a9a; font-size: 11px; font-family: 'Cascadia Code', 'Consolas', monospace; padding: 3px 8px; }
QStatusBar::item { border: none; }

QSplitter::handle { background-color: #c8d8e8; width: 1px; }
QSplitter::handle:hover { background-color: #0969da44; }

QFrame#chat_message_sent { background-color: #ddf4ff; border: 1px solid #0969da44; border-radius: 10px; padding: 8px 14px; }
QFrame#chat_message_received { background-color: #f6f8fa; border: 1px solid #c8d8e8; border-radius: 10px; padding: 8px 14px; }
QLabel#chat_username { color: #0969da; font-weight: bold; font-size: 11px; font-family: 'Cascadia Code', 'Consolas', monospace; }
QLabel#chat_time { color: #8c959f; font-size: 10px; font-family: 'Cascadia Code', 'Consolas', monospace; }

QFrame#toast { background-color: #ffffff; border: 1px solid #c8d8e8; border-radius: 10px; padding: 12px 16px; }
QFrame#toast_success { border-left: 4px solid #2da44e; background-color: #f0fff4; }
QFrame#toast_error { border-left: 4px solid #cf222e; background-color: #fff0f0; }
QFrame#toast_warning { border-left: 4px solid #bf8700; background-color: #fffbe0; }
QFrame#toast_info { border-left: 4px solid #0969da; background-color: #f0f8ff; }

QLabel#log_debug   { color: #8c959f; }
QLabel#log_info    { color: #0969da; }
QLabel#log_warning { color: #bf8700; }
QLabel#log_error   { color: #cf222e; font-weight: bold; }
"""

