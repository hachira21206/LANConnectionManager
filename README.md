# 🌐 LAN Connection Manager

A comprehensive desktop application for managing and monitoring Local Area Network (LAN) connections, built with **Python** and **PySide6**.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![PySide6](https://img.shields.io/badge/PySide6-6.5+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📋 Features

### 🏠 Dashboard
- Network overview (interface, IPv4, subnet, gateway, CIDR)
- Real-time statistics (devices, connections, traffic speed)
- Auto-refresh every 5 seconds

### 💻 Device Scanner
- Scan entire LAN subnet automatically
- Custom subnet (CIDR) or IP range scanning
- Concurrent ping with configurable thread count
- Hostname resolution and MAC address detection
- Progress bar with cancel support
- Search and filter devices

### 🔗 Connection Manager
- View all active TCP/UDP connections (via `psutil`)
- Process name and PID resolution
- Filter by protocol (TCP/UDP)
- Search and sort

### 🖥️ TCP Server/Client
- Multi-client TCP server (ThreadPoolExecutor)
- TCP client with connect/disconnect/send/receive
- Real-time message log
- Server broadcast to all clients

### 📡 UDP Communication
- UDP listener on configurable port
- Send UDP messages to any IP:port
- Message log with timestamps

### 💬 LAN Chat
- TCP-based messenger for LAN
- Host or join chat rooms
- Username support
- Message timestamps
- HTML-styled chat display

### 📁 File Transfer
- Send/receive files over TCP
- Chunked transfer (8KB chunks, memory efficient)
- Progress bar with speed display
- Auto-rename on conflict
- Error handling for disconnections

### 📊 Network Monitor
- Real-time download/upload speed charts (QPainter)
- Per-interface monitoring
- Packets sent/received counters
- Total bytes statistics
- Pause/Resume/Clear controls

### 📋 Logs
- Application event logging (INFO/WARNING/ERROR/DEBUG)
- Real-time log viewer with level filtering
- Search logs
- Export to text file
- Clear logs

### ⚙️ Settings
- Network: scan timeout, ports, thread count
- Appearance: Dark/Light theme
- Logging: log level configuration
- Database: path display, backup

### 🎨 UI/UX
- Modern dark and light themes (GitHub-inspired)
- Sidebar navigation
- Toast notifications
- Responsive layout

---

## 🛠️ Tech Stack

| Technology | Purpose |
|-----------|---------|
| Python 3.11+ | Core language |
| PySide6 | Desktop GUI framework |
| socket | TCP/UDP networking |
| threading / ThreadPoolExecutor | Concurrent operations |
| psutil | System & network monitoring |
| sqlite3 | Local database |
| ipaddress | IP/subnet operations |
| subprocess | System ping |
| logging | Application logging |
| dataclasses | Type-safe data models |

---

## 🏗️ Architecture

```
LANConnectionManager/
│
├── main.py                  # Entry point
├── requirements.txt         # Dependencies
├── README.md
├── .gitignore
│
├── app/                     # Configuration
│   ├── config.py            # App settings & defaults
│   └── constants.py         # Enums, themes, UI constants
│
├── network/                 # Network layer
│   ├── scanner.py           # LAN scanner (QThread + ThreadPoolExecutor)
│   ├── ping.py              # System ping wrapper
│   ├── socket_manager.py    # TCP Server/Client, UDP, Chat, File Transfer
│   ├── connection.py        # Active connection monitor (psutil)
│   ├── traffic_monitor.py   # Real-time traffic stats
│   └── network_utils.py     # IP/subnet utilities
│
├── database/                # Data layer
│   ├── database.py          # SQLite manager (thread-safe)
│   ├── models.py            # Dataclass models
│   └── repository.py        # CRUD repositories
│
├── services/                # Business logic
│   ├── device_service.py    # Device management
│   ├── connection_service.py # Connection & transfer management
│   └── monitoring_service.py # Monitoring orchestration
│
├── ui/                      # PySide6 UI
│   ├── main_window.py       # Main window + sidebar + toast
│   ├── dashboard.py         # Dashboard page
│   ├── devices_page.py      # Device scanner page
│   ├── connections_page.py  # Connections (TCP/UDP/Chat/File)
│   ├── monitor_page.py      # Traffic monitor + charts
│   ├── logs_page.py         # Log viewer
│   ├── settings_page.py     # Settings page
│   └── dialogs/             # Dialog windows
│
├── utils/                   # Utilities
│   ├── logger.py            # Logging setup + in-memory handler
│   ├── validators.py        # Input validation
│   └── helpers.py           # Formatting helpers
│
├── data/                    # Auto-created
│   └── lan_manager.db       # SQLite database
│
├── logs/                    # Auto-created
│   └── app.log              # Log file
│
└── tests/                   # Unit & integration tests
    ├── test_network.py      # Validator & utility tests
    ├── test_database.py     # Database CRUD tests
    └── test_services.py     # Service & TCP/UDP integration tests
```

---

## 📦 Installation

### Prerequisites
- Python 3.11 or higher
- pip package manager

### Steps

1. **Clone or download the project:**
```bash
cd LANConnectionManager
```

2. **Create virtual environment (recommended):**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

---

## 🚀 Running

```bash
python main.py
```

The application will:
1. Initialize the SQLite database automatically
2. Set up logging (file + console)
3. Load saved settings
4. Display the main window with the Dashboard

---

## 🧪 Running Tests

```bash
# Run all tests
python -m unittest discover tests -v

# Run specific test file
python -m unittest tests.test_network -v
python -m unittest tests.test_database -v
python -m unittest tests.test_services -v
```

---

## 🔥 Firewall Configuration

To enable LAN communication, you may need to allow the application through the firewall.

### Windows - Allow Specific Port

**Do NOT disable the entire firewall.** Instead, open only the ports you need:

```powershell
# Allow TCP port 5000 (for TCP Server)
netsh advfirewall firewall add rule name="LAN Manager TCP" dir=in action=allow protocol=TCP localport=5000

# Allow UDP port 5001
netsh advfirewall firewall add rule name="LAN Manager UDP" dir=in action=allow protocol=UDP localport=5001

# Allow Chat port 5002
netsh advfirewall firewall add rule name="LAN Manager Chat" dir=in action=allow protocol=TCP localport=5002

# Allow File Transfer port 5003
netsh advfirewall firewall add rule name="LAN Manager File" dir=in action=allow protocol=TCP localport=5003
```

To remove the rules later:
```powershell
netsh advfirewall firewall delete rule name="LAN Manager TCP"
netsh advfirewall firewall delete rule name="LAN Manager UDP"
netsh advfirewall firewall delete rule name="LAN Manager Chat"
netsh advfirewall firewall delete rule name="LAN Manager File"
```

### Windows - Allow Python
```powershell
netsh advfirewall firewall add rule name="Python LAN" dir=in action=allow program="C:\Python311\python.exe" enable=yes
```

---

## 🧪 LAN Testing Guide

### Testing Between Two Computers

#### Machine A (Server) — IP: 192.168.1.10

1. Start the application: `python main.py`
2. Go to **Connections → TCP Server** tab
3. Set Port to `5000`
4. Click **Start Server**
5. Status should show: `🟢 Running on port 5000`

#### Machine B (Client) — IP: 192.168.1.11

1. Start the application: `python main.py`
2. Go to **Connections → TCP Client** tab
3. Enter Server IP: `192.168.1.10`
4. Set Port: `5000`
5. Click **Connect**
6. Send a message — it should appear on Machine A's server log

#### Testing Chat

1. Machine A: Go to **Chat** tab → Enter username → Click **Host Chat**
2. Machine B: Go to **Chat** tab → Enter username → Enter Machine A's IP → Click **Join Chat**
3. Both machines can now exchange messages

#### Testing File Transfer

1. Machine A: Go to **File Transfer** tab → Click **Start Receiving** (port 5003)
2. Machine B: Enter Machine A's IP → Browse file → Click **Send**
3. File will be saved to Machine A's Downloads folder

#### Testing UDP

1. Machine A: Start UDP listener on port 5001
2. Machine B: Enter Machine A's IP, port 5001, type message → Send
3. Message appears in Machine A's UDP log

#### Testing LAN Scanner

1. Go to **Devices** page
2. Select **Auto-detect Subnet**
3. Click **Scan Network**
4. Online devices will appear in the table

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| **Port already in use** | Change to a different port number |
| **Connection refused** | Check firewall, ensure server is running on target machine |
| **Connection timeout** | Verify both machines are on the same LAN subnet |
| **Access denied (connections)** | Run as Administrator for `psutil.net_connections()` |
| **Scan finds no devices** | Check network adapter is connected, try manual IP range |
| **MAC address shows N/A** | Normal for some devices; ARP table may not have entry |
| **UI freezes** | Should not happen (all operations run in background threads) |
| **Database error** | Delete `data/lan_manager.db` and restart (auto-recreated) |

---

## 📝 Notes

- The application works **entirely offline** — no internet connection required
- All data is stored locally in SQLite (`data/lan_manager.db`)
- Logs are stored in `logs/app.log` with automatic rotation (5MB max)
- The application only scans **private/LAN IP ranges** by design
- Running as Administrator may be required for some features (active connections, MAC resolution)

---

## 📄 License

This project is for educational purposes (Networking Programming course).
