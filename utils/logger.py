"""Logging setup with file and in-memory handler for UI display."""
import logging
import logging.handlers
from pathlib import Path
from typing import List, Optional
from collections import deque
from datetime import datetime


class InMemoryHandler(logging.Handler):
    """Custom handler that stores log records in memory for UI display."""

    def __init__(self, max_records: int = 2000):
        super().__init__()
        self.records: deque = deque(maxlen=max_records)
        self._callback = None

    def emit(self, record: logging.LogRecord) -> None:
        """Store log record and notify callback."""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            'level': record.levelname,
            'module': record.module,
            'message': self.format(record),
        }
        self.records.append(log_entry)
        if self._callback:
            try:
                self._callback(log_entry)
            except Exception:
                pass

    def set_callback(self, callback) -> None:
        """Set a callback function for new log entries.

        Args:
            callback: Function that receives a log_entry dict.
        """
        self._callback = callback

    def get_records(self, level: Optional[str] = None) -> List[dict]:
        """Get stored log records with optional level filter.

        Args:
            level: Optional level filter (DEBUG, INFO, WARNING, ERROR).

        Returns:
            List of log entry dictionaries.
        """
        if level and level != "ALL":
            return [r for r in self.records if r['level'] == level]
        return list(self.records)

    def clear(self) -> None:
        """Clear all stored records."""
        self.records.clear()


# Global in-memory handler
memory_handler = InMemoryHandler()


def setup_logging(log_file: str, log_level: str = "INFO") -> None:
    """Configure application logging.

    Args:
        log_file: Path to log file.
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR).
    """
    # Ensure log directory exists
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Log format
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(module)-15s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(fmt)
    root_logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    root_logger.addHandler(console_handler)

    # In-memory handler for UI
    memory_handler.setFormatter(fmt)
    root_logger.addHandler(memory_handler)

    logging.info("Logging initialized at level %s", log_level)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)
