"""Data models using dataclasses for type-safe code."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Device:
    """Represents a network device."""
    id: Optional[int] = None
    ip_address: str = ""
    hostname: str = ""
    mac_address: str = ""
    status: str = "UNKNOWN"
    response_time: Optional[float] = None
    last_seen: Optional[str] = None
    first_discovered: Optional[str] = None
    notes: str = ""

    @property
    def is_online(self) -> bool:
        return self.status == "ONLINE"


@dataclass
class Connection:
    """Represents a network connection record."""
    id: Optional[int] = None
    local_address: str = ""
    local_port: int = 0
    remote_address: str = ""
    remote_port: int = 0
    protocol: str = "TCP"
    state: str = "UNKNOWN"
    pid: Optional[int] = None
    process_name: str = ""
    timestamp: Optional[str] = None


@dataclass
class NetworkLog:
    """Represents a log entry."""
    id: Optional[int] = None
    timestamp: Optional[str] = None
    level: str = "INFO"
    module: str = ""
    message: str = ""


@dataclass
class Transfer:
    """Represents a file transfer record."""
    id: Optional[int] = None
    filename: str = ""
    file_size: int = 0
    direction: str = "SEND"  # SEND or RECEIVE
    remote_address: str = ""
    remote_port: int = 0
    status: str = "PENDING"
    bytes_transferred: int = 0
    speed: float = 0.0
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    error_message: str = ""


@dataclass
class Setting:
    """Represents an application setting."""
    key: str = ""
    value: str = ""
    category: str = "general"


@dataclass
class ChatMessage:
    """Represents a chat message."""
    id: Optional[int] = None
    username: str = ""
    message: str = ""
    ip_address: str = ""
    timestamp: Optional[str] = None
    is_sent: bool = False


@dataclass
class DeviceInfo:
    """Extended device info for display."""
    ip_address: str = ""
    hostname: str = ""
    mac_address: str = ""
    status: str = "UNKNOWN"
    response_time: Optional[float] = None
    vendor: str = ""
    os_guess: str = ""


@dataclass
class TrafficStats:
    """Traffic statistics snapshot."""
    bytes_sent: int = 0
    bytes_recv: int = 0
    packets_sent: int = 0
    packets_recv: int = 0
    download_speed: float = 0.0
    upload_speed: float = 0.0
    timestamp: float = 0.0
