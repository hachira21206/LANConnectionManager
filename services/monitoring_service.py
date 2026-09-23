"""Monitoring service for traffic and system stats."""
import logging

from database.database import DatabaseManager
from database.repository import LogRepository
from database.models import NetworkLog
from network.connection import ConnectionMonitor

logger = logging.getLogger(__name__)


class MonitoringService:
    """Orchestrates monitoring and log storage."""

    def __init__(self, db: DatabaseManager):
        self.log_repo = LogRepository(db)
        self.connection_monitor = ConnectionMonitor()

    def log_event(self, level: str, module: str, message: str) -> None:
        """Log an application event to database.

        Args:
            level: Log level (INFO, WARNING, ERROR, DEBUG).
            module: Source module name.
            message: Log message.
        """
        log = NetworkLog(level=level, module=module, message=message)
        try:
            self.log_repo.add(log)
        except Exception as e:
            logger.error("Failed to save log: %s", e)

    def get_logs(self, level: str = None, limit: int = 500) -> list:
        """Get application logs."""
        return self.log_repo.get_all(level, limit)

    def search_logs(self, query: str) -> list:
        """Search logs by message."""
        return self.log_repo.search(query)

    def clear_logs(self) -> None:
        """Clear all logs."""
        self.log_repo.clear()
        logger.info("Logs cleared")

    def get_connection_stats(self) -> dict:
        """Get current connection statistics."""
        return self.connection_monitor.count_connections()

    def get_active_connections(self, protocol: str = None) -> list:
        """Get active network connections."""
        return self.connection_monitor.get_connections(protocol)
