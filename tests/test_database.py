"""Tests for database operations."""
import sys
import os
import unittest
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import DatabaseManager
from database.repository import (
    DeviceRepository, ConnectionRepository, LogRepository,
    TransferRepository, SettingsRepository, ChatRepository
)
from database.models import Device, Connection, NetworkLog, Transfer, Setting, ChatMessage


class TestDatabaseManager(unittest.TestCase):
    """Test DatabaseManager initialization and operations."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        # Reset singleton
        DatabaseManager._instance = None
        self.db = DatabaseManager(self.db_path)

    def tearDown(self):
        self.db.close()
        DatabaseManager._instance = None
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_database_creation(self):
        """Test that database file is created."""
        self.assertTrue(os.path.exists(self.db_path))

    def test_tables_created(self):
        """Test that all tables are created."""
        conn = self.db.get_connection()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row['name'] for row in cursor.fetchall()}
        expected = {'devices', 'connections', 'network_logs',
                    'transfers', 'settings', 'chat_messages'}
        self.assertTrue(expected.issubset(tables))

    def test_execute_and_fetch(self):
        """Test basic execute and fetch."""
        self.db.execute(
            "INSERT INTO settings (key, value, category) VALUES (?, ?, ?)",
            ("test_key", "test_value", "test")
        )
        row = self.db.fetch_one(
            "SELECT value FROM settings WHERE key = ?", ("test_key",)
        )
        self.assertIsNotNone(row)
        self.assertEqual(row['value'], "test_value")

    def test_fetch_all(self):
        """Test fetch_all operation."""
        for i in range(5):
            self.db.execute(
                "INSERT INTO settings (key, value, category) VALUES (?, ?, ?)",
                (f"key_{i}", f"value_{i}", "test")
            )
        rows = self.db.fetch_all(
            "SELECT * FROM settings WHERE category = ?", ("test",)
        )
        self.assertEqual(len(rows), 5)


class TestDeviceRepository(unittest.TestCase):
    """Test DeviceRepository CRUD."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        DatabaseManager._instance = None
        self.db = DatabaseManager(self.db_path)
        self.repo = DeviceRepository(self.db)

    def tearDown(self):
        self.db.close()
        DatabaseManager._instance = None
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_upsert_new_device(self):
        """Test inserting a new device."""
        device = Device(
            ip_address="192.168.1.1",
            hostname="Router",
            mac_address="AA:BB:CC:DD:EE:FF",
            status="ONLINE",
            response_time=2.5
        )
        device_id = self.repo.upsert(device)
        self.assertIsNotNone(device_id)

    def test_upsert_update_device(self):
        """Test updating an existing device."""
        device = Device(ip_address="192.168.1.1", status="ONLINE")
        self.repo.upsert(device)

        device.status = "OFFLINE"
        self.repo.upsert(device)

        result = self.repo.get_by_ip("192.168.1.1")
        self.assertEqual(result.status, "OFFLINE")

    def test_get_all(self):
        """Test getting all devices."""
        for i in range(3):
            self.repo.upsert(Device(
                ip_address=f"192.168.1.{i+1}", status="ONLINE"
            ))
        devices = self.repo.get_all()
        self.assertEqual(len(devices), 3)

    def test_get_by_status(self):
        """Test filtering by status."""
        self.repo.upsert(Device(ip_address="192.168.1.1", status="ONLINE"))
        self.repo.upsert(Device(ip_address="192.168.1.2", status="OFFLINE"))
        self.repo.upsert(Device(ip_address="192.168.1.3", status="ONLINE"))

        online = self.repo.get_by_status("ONLINE")
        self.assertEqual(len(online), 2)

        offline = self.repo.get_by_status("OFFLINE")
        self.assertEqual(len(offline), 1)

    def test_count(self):
        """Test device counting."""
        self.repo.upsert(Device(ip_address="192.168.1.1", status="ONLINE"))
        self.repo.upsert(Device(ip_address="192.168.1.2", status="OFFLINE"))

        self.assertEqual(self.repo.count(), 2)
        self.assertEqual(self.repo.count("ONLINE"), 1)
        self.assertEqual(self.repo.count("OFFLINE"), 1)

    def test_delete(self):
        """Test device deletion."""
        self.repo.upsert(Device(ip_address="192.168.1.1"))
        self.repo.delete("192.168.1.1")
        self.assertIsNone(self.repo.get_by_ip("192.168.1.1"))

    def test_set_all_offline(self):
        """Test marking all devices offline."""
        self.repo.upsert(Device(ip_address="192.168.1.1", status="ONLINE"))
        self.repo.upsert(Device(ip_address="192.168.1.2", status="ONLINE"))
        self.repo.set_all_offline()

        self.assertEqual(self.repo.count("ONLINE"), 0)
        self.assertEqual(self.repo.count("OFFLINE"), 2)


class TestConnectionRepository(unittest.TestCase):
    """Test ConnectionRepository."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        DatabaseManager._instance = None
        self.db = DatabaseManager(self.db_path)
        self.repo = ConnectionRepository(self.db)

    def tearDown(self):
        self.db.close()
        DatabaseManager._instance = None
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_add_connection(self):
        """Test adding a connection record."""
        conn = Connection(
            local_address="192.168.1.10",
            local_port=5000,
            remote_address="192.168.1.1",
            remote_port=443,
            protocol="TCP",
            state="ESTABLISHED"
        )
        conn_id = self.repo.add(conn)
        self.assertIsNotNone(conn_id)

    def test_get_recent(self):
        """Test getting recent connections."""
        for i in range(5):
            self.repo.add(Connection(
                local_address="192.168.1.10",
                local_port=5000 + i,
                protocol="TCP"
            ))
        recent = self.repo.get_recent(limit=3)
        self.assertEqual(len(recent), 3)

    def test_get_by_protocol(self):
        """Test filtering by protocol."""
        self.repo.add(Connection(
            local_address="192.168.1.10", local_port=80, protocol="TCP"
        ))
        self.repo.add(Connection(
            local_address="192.168.1.10", local_port=53, protocol="UDP"
        ))

        tcp = self.repo.get_by_protocol("TCP")
        self.assertEqual(len(tcp), 1)


class TestSettingsRepository(unittest.TestCase):
    """Test SettingsRepository."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        DatabaseManager._instance = None
        self.db = DatabaseManager(self.db_path)
        self.repo = SettingsRepository(self.db)

    def tearDown(self):
        self.db.close()
        DatabaseManager._instance = None
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_set_and_get(self):
        """Test setting and getting values."""
        self.repo.set("theme", "dark", "appearance")
        self.assertEqual(self.repo.get("theme"), "dark")

    def test_get_default(self):
        """Test default value for missing key."""
        self.assertEqual(
            self.repo.get("nonexistent", "default_val"),
            "default_val"
        )

    def test_update_setting(self):
        """Test updating an existing setting."""
        self.repo.set("port", "5000")
        self.repo.set("port", "8080")
        self.assertEqual(self.repo.get("port"), "8080")

    def test_get_all(self):
        """Test getting all settings."""
        self.repo.set("key1", "val1")
        self.repo.set("key2", "val2")
        all_settings = self.repo.get_all()
        self.assertEqual(len(all_settings), 2)


class TestLogRepository(unittest.TestCase):
    """Test LogRepository."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        DatabaseManager._instance = None
        self.db = DatabaseManager(self.db_path)
        self.repo = LogRepository(self.db)

    def tearDown(self):
        self.db.close()
        DatabaseManager._instance = None
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_add_log(self):
        """Test adding a log entry."""
        log = NetworkLog(level="INFO", module="test", message="Test message")
        log_id = self.repo.add(log)
        self.assertIsNotNone(log_id)

    def test_get_by_level(self):
        """Test filtering logs by level."""
        self.repo.add(NetworkLog(level="INFO", module="a", message="info"))
        self.repo.add(NetworkLog(level="ERROR", module="b", message="error"))
        self.repo.add(NetworkLog(level="INFO", module="c", message="info2"))

        info_logs = self.repo.get_all(level="INFO")
        self.assertEqual(len(info_logs), 2)

        error_logs = self.repo.get_all(level="ERROR")
        self.assertEqual(len(error_logs), 1)

    def test_search(self):
        """Test searching logs."""
        self.repo.add(NetworkLog(
            level="INFO", module="scanner", message="Device 192.168.1.1 found"
        ))
        self.repo.add(NetworkLog(
            level="ERROR", module="server", message="Connection failed"
        ))

        results = self.repo.search("Device")
        self.assertEqual(len(results), 1)

    def test_clear(self):
        """Test clearing logs."""
        self.repo.add(NetworkLog(level="INFO", module="t", message="msg"))
        self.repo.clear()
        self.assertEqual(self.repo.count(), 0)


if __name__ == "__main__":
    unittest.main()
