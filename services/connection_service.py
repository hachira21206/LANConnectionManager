"""Connection management service."""
import logging
from typing import List

from database.database import DatabaseManager
from database.repository import ConnectionRepository, TransferRepository
from database.models import Connection, Transfer

logger = logging.getLogger(__name__)


class ConnectionService:
    """Business logic for connection management."""

    def __init__(self, db: DatabaseManager):
        self.conn_repo = ConnectionRepository(db)
        self.transfer_repo = TransferRepository(db)

    def log_connection(self, connection: Connection) -> int:
        """Log a connection event.

        Args:
            connection: Connection to log.

        Returns:
            Row ID.
        """
        conn_id = self.conn_repo.add(connection)
        logger.debug("Connection logged: %s:%d -> %s:%d (%s)",
                      connection.local_address, connection.local_port,
                      connection.remote_address, connection.remote_port,
                      connection.protocol)
        return conn_id

    def get_connection_history(self, limit: int = 100) -> List[Connection]:
        """Get recent connection history."""
        return self.conn_repo.get_recent(limit)

    def get_tcp_history(self, limit: int = 100) -> List[Connection]:
        """Get TCP connection history."""
        return self.conn_repo.get_by_protocol("TCP", limit)

    def get_udp_history(self, limit: int = 100) -> List[Connection]:
        """Get UDP connection history."""
        return self.conn_repo.get_by_protocol("UDP", limit)

    def clear_history(self) -> None:
        """Clear all connection history."""
        self.conn_repo.clear()
        logger.info("Connection history cleared")

    # File transfers
    def log_transfer(self, transfer: Transfer) -> int:
        """Log a file transfer.

        Args:
            transfer: Transfer to log.

        Returns:
            Row ID.
        """
        return self.transfer_repo.add(transfer)

    def update_transfer(self, transfer_id: int, status: str,
                        bytes_transferred: int = 0, speed: float = 0.0,
                        error: str = "") -> None:
        """Update a transfer status."""
        self.transfer_repo.update_status(
            transfer_id, status, bytes_transferred, speed, error
        )

    def get_transfers(self, limit: int = 50) -> List[Transfer]:
        """Get transfer history."""
        return self.transfer_repo.get_all(limit)
