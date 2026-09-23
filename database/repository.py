"""Repository pattern implementation for database operations."""
import logging
from typing import List, Optional
from datetime import datetime

from database.database import DatabaseManager
from database.models import Device, Connection, NetworkLog, Transfer, Setting, ChatMessage

logger = logging.getLogger(__name__)


class DeviceRepository:
    """Repository for device CRUD operations."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def upsert(self, device: Device) -> int:
        """Insert or update a device.

        Args:
            device: Device object to save.

        Returns:
            Row ID of the device.
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = self.db.execute(
            """INSERT INTO devices (ip_address, hostname, mac_address, status,
                   response_time, last_seen, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(ip_address) DO UPDATE SET
                   hostname = excluded.hostname,
                   mac_address = CASE WHEN excluded.mac_address != '' 
                       THEN excluded.mac_address ELSE devices.mac_address END,
                   status = excluded.status,
                   response_time = excluded.response_time,
                   last_seen = excluded.last_seen,
                   notes = CASE WHEN excluded.notes != '' 
                       THEN excluded.notes ELSE devices.notes END
            """,
            (device.ip_address, device.hostname, device.mac_address,
             device.status, device.response_time, now, device.notes)
        )
        return cursor.lastrowid

    def get_all(self) -> List[Device]:
        """Get all devices.

        Returns:
            List of Device objects.
        """
        rows = self.db.fetch_all(
            "SELECT * FROM devices ORDER BY ip_address"
        )
        return [self._row_to_device(row) for row in rows]

    def get_by_status(self, status: str) -> List[Device]:
        """Get devices by status.

        Args:
            status: Device status filter.

        Returns:
            List of Device objects matching status.
        """
        rows = self.db.fetch_all(
            "SELECT * FROM devices WHERE status = ? ORDER BY ip_address",
            (status,)
        )
        return [self._row_to_device(row) for row in rows]

    def get_by_ip(self, ip_address: str) -> Optional[Device]:
        """Get device by IP address.

        Args:
            ip_address: IP address to search.

        Returns:
            Device or None.
        """
        row = self.db.fetch_one(
            "SELECT * FROM devices WHERE ip_address = ?",
            (ip_address,)
        )
        return self._row_to_device(row) if row else None

    def count(self, status: Optional[str] = None) -> int:
        """Count devices, optionally filtered by status.

        Args:
            status: Optional status filter.

        Returns:
            Device count.
        """
        if status:
            row = self.db.fetch_one(
                "SELECT COUNT(*) as cnt FROM devices WHERE status = ?",
                (status,)
            )
        else:
            row = self.db.fetch_one("SELECT COUNT(*) as cnt FROM devices")
        return row['cnt'] if row else 0

    def delete(self, ip_address: str) -> None:
        """Delete a device by IP.

        Args:
            ip_address: IP address of device to delete.
        """
        self.db.execute("DELETE FROM devices WHERE ip_address = ?", (ip_address,))

    def set_all_offline(self) -> None:
        """Mark all devices as offline."""
        self.db.execute("UPDATE devices SET status = 'OFFLINE'")

    def update_notes(self, ip_address: str, notes: str) -> None:
        """Update device notes.

        Args:
            ip_address: Device IP.
            notes: Notes text.
        """
        self.db.execute(
            "UPDATE devices SET notes = ? WHERE ip_address = ?",
            (notes, ip_address)
        )

    @staticmethod
    def _row_to_device(row) -> Device:
        """Convert a database row to Device model."""
        return Device(
            id=row['id'],
            ip_address=row['ip_address'],
            hostname=row['hostname'],
            mac_address=row['mac_address'],
            status=row['status'],
            response_time=row['response_time'],
            last_seen=row['last_seen'],
            first_discovered=row['first_discovered'],
            notes=row['notes']
        )


class ConnectionRepository:
    """Repository for connection history."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def add(self, connection: Connection) -> int:
        """Add a connection record.

        Args:
            connection: Connection to save.

        Returns:
            Row ID.
        """
        cursor = self.db.execute(
            """INSERT INTO connections (local_address, local_port, remote_address,
                   remote_port, protocol, state, pid, process_name)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (connection.local_address, connection.local_port,
             connection.remote_address, connection.remote_port,
             connection.protocol, connection.state,
             connection.pid, connection.process_name)
        )
        return cursor.lastrowid

    def get_recent(self, limit: int = 100) -> List[Connection]:
        """Get recent connections.

        Args:
            limit: Maximum number of records.

        Returns:
            List of Connection objects.
        """
        rows = self.db.fetch_all(
            "SELECT * FROM connections ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        return [self._row_to_connection(row) for row in rows]

    def get_by_protocol(self, protocol: str, limit: int = 100) -> List[Connection]:
        """Get connections filtered by protocol.

        Args:
            protocol: TCP or UDP.
            limit: Maximum records.

        Returns:
            List of Connection objects.
        """
        rows = self.db.fetch_all(
            "SELECT * FROM connections WHERE protocol = ? ORDER BY timestamp DESC LIMIT ?",
            (protocol, limit)
        )
        return [self._row_to_connection(row) for row in rows]

    def clear(self) -> None:
        """Clear all connection history."""
        self.db.execute("DELETE FROM connections")

    @staticmethod
    def _row_to_connection(row) -> Connection:
        return Connection(
            id=row['id'],
            local_address=row['local_address'],
            local_port=row['local_port'],
            remote_address=row['remote_address'],
            remote_port=row['remote_port'],
            protocol=row['protocol'],
            state=row['state'],
            pid=row['pid'],
            process_name=row['process_name'],
            timestamp=row['timestamp']
        )


class LogRepository:
    """Repository for application logs."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def add(self, log: NetworkLog) -> int:
        """Add a log entry.

        Args:
            log: NetworkLog to save.

        Returns:
            Row ID.
        """
        cursor = self.db.execute(
            "INSERT INTO network_logs (level, module, message) VALUES (?, ?, ?)",
            (log.level, log.module, log.message)
        )
        return cursor.lastrowid

    def get_all(self, level: Optional[str] = None, limit: int = 500) -> List[NetworkLog]:
        """Get log entries with optional level filter.

        Args:
            level: Optional log level filter.
            limit: Maximum number of records.

        Returns:
            List of NetworkLog objects.
        """
        if level and level != "ALL":
            rows = self.db.fetch_all(
                "SELECT * FROM network_logs WHERE level = ? ORDER BY timestamp DESC LIMIT ?",
                (level, limit)
            )
        else:
            rows = self.db.fetch_all(
                "SELECT * FROM network_logs ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
        return [self._row_to_log(row) for row in rows]

    def search(self, query: str, limit: int = 100) -> List[NetworkLog]:
        """Search logs by message content.

        Args:
            query: Search string.
            limit: Maximum records.

        Returns:
            Matching NetworkLog objects.
        """
        rows = self.db.fetch_all(
            "SELECT * FROM network_logs WHERE message LIKE ? ORDER BY timestamp DESC LIMIT ?",
            (f"%{query}%", limit)
        )
        return [self._row_to_log(row) for row in rows]

    def clear(self) -> None:
        """Clear all logs."""
        self.db.execute("DELETE FROM network_logs")

    def count(self) -> int:
        """Count total log entries."""
        row = self.db.fetch_one("SELECT COUNT(*) as cnt FROM network_logs")
        return row['cnt'] if row else 0

    @staticmethod
    def _row_to_log(row) -> NetworkLog:
        return NetworkLog(
            id=row['id'],
            timestamp=row['timestamp'],
            level=row['level'],
            module=row['module'],
            message=row['message']
        )


class TransferRepository:
    """Repository for file transfer records."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def add(self, transfer: Transfer) -> int:
        """Add a transfer record.

        Args:
            transfer: Transfer to save.

        Returns:
            Row ID.
        """
        cursor = self.db.execute(
            """INSERT INTO transfers (filename, file_size, direction, remote_address,
                   remote_port, status, bytes_transferred, speed, error_message)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (transfer.filename, transfer.file_size, transfer.direction,
             transfer.remote_address, transfer.remote_port, transfer.status,
             transfer.bytes_transferred, transfer.speed, transfer.error_message)
        )
        return cursor.lastrowid

    def update_status(self, transfer_id: int, status: str,
                      bytes_transferred: int = 0, speed: float = 0.0,
                      error_message: str = "") -> None:
        """Update transfer status.

        Args:
            transfer_id: ID of the transfer.
            status: New status.
            bytes_transferred: Bytes transferred so far.
            speed: Transfer speed.
            error_message: Error message if failed.
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.execute(
            """UPDATE transfers SET status = ?, bytes_transferred = ?,
                   speed = ?, error_message = ?, end_time = ?
               WHERE id = ?""",
            (status, bytes_transferred, speed, error_message, now, transfer_id)
        )

    def get_all(self, limit: int = 100) -> List[Transfer]:
        """Get recent transfers.

        Returns:
            List of Transfer objects.
        """
        rows = self.db.fetch_all(
            "SELECT * FROM transfers ORDER BY start_time DESC LIMIT ?",
            (limit,)
        )
        return [self._row_to_transfer(row) for row in rows]

    @staticmethod
    def _row_to_transfer(row) -> Transfer:
        return Transfer(
            id=row['id'],
            filename=row['filename'],
            file_size=row['file_size'],
            direction=row['direction'],
            remote_address=row['remote_address'],
            remote_port=row['remote_port'],
            status=row['status'],
            bytes_transferred=row['bytes_transferred'],
            speed=row['speed'],
            start_time=row['start_time'],
            end_time=row['end_time'],
            error_message=row['error_message']
        )


class SettingsRepository:
    """Repository for application settings."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def get(self, key: str, default: str = "") -> str:
        """Get a setting value.

        Args:
            key: Setting key.
            default: Default value if not found.

        Returns:
            Setting value or default.
        """
        row = self.db.fetch_one(
            "SELECT value FROM settings WHERE key = ?", (key,)
        )
        return row['value'] if row else default

    def set(self, key: str, value: str, category: str = "general") -> None:
        """Set a setting value.

        Args:
            key: Setting key.
            value: Setting value.
            category: Setting category.
        """
        self.db.execute(
            """INSERT INTO settings (key, value, category)
               VALUES (?, ?, ?)
               ON CONFLICT(key) DO UPDATE SET value = excluded.value""",
            (key, value, category)
        )

    def get_by_category(self, category: str) -> List[Setting]:
        """Get all settings in a category.

        Args:
            category: Category name.

        Returns:
            List of Setting objects.
        """
        rows = self.db.fetch_all(
            "SELECT * FROM settings WHERE category = ?", (category,)
        )
        return [Setting(key=row['key'], value=row['value'],
                        category=row['category']) for row in rows]

    def get_all(self) -> dict:
        """Get all settings as a dictionary.

        Returns:
            Dict of key-value settings.
        """
        rows = self.db.fetch_all("SELECT key, value FROM settings")
        return {row['key']: row['value'] for row in rows}

    def delete(self, key: str) -> None:
        """Delete a setting.

        Args:
            key: Setting key to delete.
        """
        self.db.execute("DELETE FROM settings WHERE key = ?", (key,))


class ChatRepository:
    """Repository for chat messages."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def add(self, msg: ChatMessage) -> int:
        """Add a chat message.

        Args:
            msg: ChatMessage to save.

        Returns:
            Row ID.
        """
        cursor = self.db.execute(
            """INSERT INTO chat_messages (username, message, ip_address, is_sent)
               VALUES (?, ?, ?, ?)""",
            (msg.username, msg.message, msg.ip_address, 1 if msg.is_sent else 0)
        )
        return cursor.lastrowid

    def get_recent(self, limit: int = 200) -> List[ChatMessage]:
        """Get recent messages.

        Args:
            limit: Maximum messages.

        Returns:
            List of ChatMessage objects.
        """
        rows = self.db.fetch_all(
            "SELECT * FROM chat_messages ORDER BY timestamp ASC LIMIT ?",
            (limit,)
        )
        return [self._row_to_message(row) for row in rows]

    def clear(self) -> None:
        """Clear all chat messages."""
        self.db.execute("DELETE FROM chat_messages")

    @staticmethod
    def _row_to_message(row) -> ChatMessage:
        return ChatMessage(
            id=row['id'],
            username=row['username'],
            message=row['message'],
            ip_address=row['ip_address'],
            timestamp=row['timestamp'],
            is_sent=bool(row['is_sent'])
        )
