"""App configuration module."""
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)


@dataclass
class AppConfig:
    """Application configuration with defaults."""

    # Application
    app_name: str = "LAN Connection Manager"
    app_version: str = "1.0.0"

    # Database
    db_path: str = str(DATA_DIR / "lan_manager.db")

    # Network defaults
    default_scan_timeout: float = 1.0
    default_tcp_port: int = 5000
    default_udp_port: int = 5001
    default_chat_port: int = 5002
    default_file_transfer_port: int = 5003
    scan_thread_count: int = 50
    scan_interval: int = 300  # seconds

    # Socket
    socket_buffer_size: int = 4096
    file_chunk_size: int = 8192
    socket_timeout: float = 5.0
    max_clients: int = 20

    # Traffic monitor
    monitor_interval: float = 1.0  # seconds

    # Logging
    log_level: str = "INFO"
    log_file: str = str(LOGS_DIR / "app.log")
    max_log_size: int = 5 * 1024 * 1024  # 5MB
    log_backup_count: int = 3

    # UI
    window_width: int = 1280
    window_height: int = 800
    theme: str = "dark"  # "dark" or "light"

    # LAN Chat
    chat_username: str = ""
    chat_discovery_port: int = 5010

    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith('_')
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AppConfig':
        """Create config from dictionary."""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


# Global config instance
config = AppConfig()
