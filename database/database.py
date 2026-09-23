"""Database manager for SQLite operations."""
import sqlite3
import threading
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database connections and schema initialization."""

    _instance: Optional['DatabaseManager'] = None
    _lock = threading.Lock()

    def __init__(self, db_path: str):
        """Initialize database manager.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self._local = threading.local()
        self._ensure_directory()
        self._init_database()

    @classmethod
    def get_instance(cls, db_path: Optional[str] = None) -> 'DatabaseManager':
        """Get or create singleton instance.

        Args:
            db_path: Path to database file (required on first call).

        Returns:
            DatabaseManager singleton instance.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    if db_path is None:
                        raise ValueError("db_path required for first initialization")
                    cls._instance = cls(db_path)
        return cls._instance

    def _ensure_directory(self) -> None:
        """Create database directory if it doesn't exist."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Get a thread-local database connection.

        Returns:
            sqlite3.Connection for the current thread.
        """
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self.db_path,
                timeout=10.0,
                check_same_thread=False
            )
            self._local.connection.row_factory = sqlite3.Row
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            self._local.connection.execute("PRAGMA foreign_keys=ON")
        return self._local.connection

    def _init_database(self) -> None:
        """Initialize database schema."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT NOT NULL,
                hostname TEXT DEFAULT '',
                mac_address TEXT DEFAULT '',
                status TEXT DEFAULT 'UNKNOWN',
                response_time REAL,
                last_seen TEXT,
                first_discovered TEXT DEFAULT (datetime('now', 'localtime')),
                notes TEXT DEFAULT '',
                UNIQUE(ip_address)
            );

            CREATE TABLE IF NOT EXISTS connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                local_address TEXT NOT NULL,
                local_port INTEGER NOT NULL,
                remote_address TEXT DEFAULT '',
                remote_port INTEGER DEFAULT 0,
                protocol TEXT DEFAULT 'TCP',
                state TEXT DEFAULT 'UNKNOWN',
                pid INTEGER,
                process_name TEXT DEFAULT '',
                timestamp TEXT DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS network_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT (datetime('now', 'localtime')),
                level TEXT DEFAULT 'INFO',
                module TEXT DEFAULT '',
                message TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_size INTEGER DEFAULT 0,
                direction TEXT DEFAULT 'SEND',
                remote_address TEXT DEFAULT '',
                remote_port INTEGER DEFAULT 0,
                status TEXT DEFAULT 'PENDING',
                bytes_transferred INTEGER DEFAULT 0,
                speed REAL DEFAULT 0.0,
                start_time TEXT DEFAULT (datetime('now', 'localtime')),
                end_time TEXT,
                error_message TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                category TEXT DEFAULT 'general'
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                message TEXT NOT NULL,
                ip_address TEXT DEFAULT '',
                timestamp TEXT DEFAULT (datetime('now', 'localtime')),
                is_sent INTEGER DEFAULT 0
            );

            -- Indexes for performance
            CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status);
            CREATE INDEX IF NOT EXISTS idx_devices_ip ON devices(ip_address);
            CREATE INDEX IF NOT EXISTS idx_connections_timestamp ON connections(timestamp);
            CREATE INDEX IF NOT EXISTS idx_logs_level ON network_logs(level);
            CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON network_logs(timestamp);
            CREATE INDEX IF NOT EXISTS idx_transfers_status ON transfers(status);
        """)

        conn.commit()
        logger.info("Database initialized successfully at %s", self.db_path)

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a query with parameters.

        Args:
            query: SQL query string.
            params: Query parameters.

        Returns:
            sqlite3.Cursor with results.
        """
        conn = self.get_connection()
        try:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor
        except sqlite3.Error as e:
            logger.error("Database error: %s | Query: %s", e, query)
            raise

    def execute_many(self, query: str, params_list: list) -> None:
        """Execute a query with multiple parameter sets.

        Args:
            query: SQL query string.
            params_list: List of parameter tuples.
        """
        conn = self.get_connection()
        try:
            conn.executemany(query, params_list)
            conn.commit()
        except sqlite3.Error as e:
            logger.error("Database error (executemany): %s", e)
            raise

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Fetch a single row.

        Args:
            query: SQL query string.
            params: Query parameters.

        Returns:
            sqlite3.Row or None.
        """
        conn = self.get_connection()
        try:
            cursor = conn.execute(query, params)
            return cursor.fetchone()
        except sqlite3.Error as e:
            logger.error("Database error (fetch_one): %s", e)
            raise

    def fetch_all(self, query: str, params: tuple = ()) -> list:
        """Fetch all rows.

        Args:
            query: SQL query string.
            params: Query parameters.

        Returns:
            List of sqlite3.Row objects.
        """
        conn = self.get_connection()
        try:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error("Database error (fetch_all): %s", e)
            raise

    def close(self) -> None:
        """Close the thread-local database connection."""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None

    def backup(self, backup_path: str) -> bool:
        """Create a database backup.

        Args:
            backup_path: Path for the backup file.

        Returns:
            True if backup was successful.
        """
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info("Database backed up to %s", backup_path)
            return True
        except Exception as e:
            logger.error("Database backup failed: %s", e)
            return False
