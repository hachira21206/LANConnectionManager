"""Integration tests for services and TCP client/server."""
import sys
import os
import time
import socket
import threading
import unittest
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import DatabaseManager
from database.models import Device, Connection
from services.device_service import DeviceService
from services.connection_service import ConnectionService


class TestDeviceService(unittest.TestCase):
    """Test DeviceService business logic."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        DatabaseManager._instance = None
        self.db = DatabaseManager(self.db_path)
        self.service = DeviceService(self.db)

    def tearDown(self):
        self.db.close()
        DatabaseManager._instance = None
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_and_get_device(self):
        """Test saving and retrieving a device."""
        device = Device(
            ip_address="192.168.1.1",
            hostname="Router",
            status="ONLINE",
            response_time=2.5
        )
        self.service.save_device(device)

        result = self.service.get_device("192.168.1.1")
        self.assertIsNotNone(result)
        self.assertEqual(result.hostname, "Router")
        self.assertEqual(result.status, "ONLINE")

    def test_save_multiple_devices(self):
        """Test saving multiple devices."""
        devices = [
            Device(ip_address=f"192.168.1.{i}", status="ONLINE")
            for i in range(1, 6)
        ]
        self.service.save_devices(devices)
        self.assertEqual(len(self.service.get_all_devices()), 5)

    def test_get_statistics(self):
        """Test statistics calculation."""
        self.service.save_device(Device(ip_address="192.168.1.1", status="ONLINE"))
        self.service.save_device(Device(ip_address="192.168.1.2", status="ONLINE"))
        self.service.save_device(Device(ip_address="192.168.1.3", status="OFFLINE"))

        stats = self.service.get_statistics()
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['online'], 2)
        self.assertEqual(stats['offline'], 1)

    def test_mark_all_offline(self):
        """Test marking all devices offline."""
        self.service.save_device(Device(ip_address="192.168.1.1", status="ONLINE"))
        self.service.save_device(Device(ip_address="192.168.1.2", status="ONLINE"))
        self.service.mark_all_offline()

        stats = self.service.get_statistics()
        self.assertEqual(stats['online'], 0)
        self.assertEqual(stats['offline'], 2)


class TestConnectionService(unittest.TestCase):
    """Test ConnectionService."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        DatabaseManager._instance = None
        self.db = DatabaseManager(self.db_path)
        self.service = ConnectionService(self.db)

    def tearDown(self):
        self.db.close()
        DatabaseManager._instance = None
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_log_connection(self):
        """Test logging a connection."""
        conn = Connection(
            local_address="192.168.1.10",
            local_port=5000,
            remote_address="192.168.1.1",
            remote_port=443,
            protocol="TCP",
            state="ESTABLISHED"
        )
        conn_id = self.service.log_connection(conn)
        self.assertIsNotNone(conn_id)

    def test_get_history(self):
        """Test getting connection history."""
        for i in range(5):
            self.service.log_connection(Connection(
                local_address="192.168.1.10",
                local_port=5000 + i,
                protocol="TCP"
            ))
        history = self.service.get_connection_history(limit=3)
        self.assertEqual(len(history), 3)


class TestTCPEchoIntegration(unittest.TestCase):
    """Integration test for basic TCP socket communication."""

    def test_tcp_echo(self):
        """Test basic TCP client/server echo communication."""
        port = 0  # Let OS assign port

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("127.0.0.1", port))
        server_socket.listen(1)
        actual_port = server_socket.getsockname()[1]

        received = []

        def server_handler():
            conn, addr = server_socket.accept()
            data = conn.recv(1024)
            received.append(data.decode())
            conn.sendall(data)  # Echo back
            conn.close()
            server_socket.close()

        server_thread = threading.Thread(target=server_handler, daemon=True)
        server_thread.start()

        # Client
        time.sleep(0.1)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("127.0.0.1", actual_port))
        client.sendall(b"Hello LAN!")
        response = client.recv(1024).decode()
        client.close()

        server_thread.join(timeout=2)

        self.assertEqual(received[0], "Hello LAN!")
        self.assertEqual(response, "Hello LAN!")

    def test_udp_echo(self):
        """Test basic UDP send/receive."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

        received = []

        def listener():
            sock.settimeout(2.0)
            try:
                data, addr = sock.recvfrom(1024)
                received.append(data.decode())
            except socket.timeout:
                pass
            finally:
                sock.close()

        thread = threading.Thread(target=listener, daemon=True)
        thread.start()

        time.sleep(0.1)
        sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sender.sendto(b"UDP Test", ("127.0.0.1", port))
        sender.close()

        thread.join(timeout=3)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0], "UDP Test")


if __name__ == "__main__":
    unittest.main()
