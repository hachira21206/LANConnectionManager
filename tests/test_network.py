"""Tests for network utilities and validators."""
import sys
import os
import unittest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.validators import (
    validate_ip, validate_port, validate_subnet,
    validate_ip_range, is_private_ip, sanitize_input, parse_ip_port
)
from utils.helpers import (
    format_bytes, format_speed, format_duration, format_ping, truncate_string
)
from network.network_utils import (
    get_local_ip, get_ip_range, get_ip_range_from_bounds, get_subnet_info
)


class TestIPValidation(unittest.TestCase):
    """Test IP address validation."""

    def test_valid_ips(self):
        self.assertTrue(validate_ip("192.168.1.1"))
        self.assertTrue(validate_ip("10.0.0.1"))
        self.assertTrue(validate_ip("255.255.255.255"))
        self.assertTrue(validate_ip("0.0.0.0"))

    def test_invalid_ips(self):
        self.assertFalse(validate_ip(""))
        self.assertFalse(validate_ip("256.1.1.1"))
        self.assertFalse(validate_ip("192.168.1"))
        self.assertFalse(validate_ip("abc.def.ghi.jkl"))
        self.assertFalse(validate_ip("192.168.1.1.1"))
        self.assertFalse(validate_ip("-1.0.0.0"))
        self.assertFalse(validate_ip("hello"))


class TestPortValidation(unittest.TestCase):
    """Test port number validation."""

    def test_valid_ports(self):
        self.assertTrue(validate_port(1))
        self.assertTrue(validate_port(80))
        self.assertTrue(validate_port(443))
        self.assertTrue(validate_port(5000))
        self.assertTrue(validate_port(65535))
        self.assertTrue(validate_port("8080"))

    def test_invalid_ports(self):
        self.assertFalse(validate_port(0))
        self.assertFalse(validate_port(-1))
        self.assertFalse(validate_port(65536))
        self.assertFalse(validate_port("abc"))
        self.assertFalse(validate_port(None))
        self.assertFalse(validate_port(""))


class TestSubnetValidation(unittest.TestCase):
    """Test subnet validation."""

    def test_valid_subnets(self):
        self.assertTrue(validate_subnet("192.168.1.0/24"))
        self.assertTrue(validate_subnet("10.0.0.0/8"))
        self.assertTrue(validate_subnet("172.16.0.0/16"))
        self.assertTrue(validate_subnet("192.168.1.0/32"))

    def test_invalid_subnets(self):
        self.assertFalse(validate_subnet(""))
        self.assertFalse(validate_subnet("192.168.1.0"))
        self.assertFalse(validate_subnet("192.168.1.0/33"))
        self.assertFalse(validate_subnet("abc/24"))


class TestIPRange(unittest.TestCase):
    """Test IP range validation and generation."""

    def test_valid_range(self):
        self.assertTrue(validate_ip_range("192.168.1.1", "192.168.1.10"))
        self.assertTrue(validate_ip_range("192.168.1.1", "192.168.1.1"))

    def test_invalid_range(self):
        self.assertFalse(validate_ip_range("192.168.1.10", "192.168.1.1"))
        self.assertFalse(validate_ip_range("abc", "192.168.1.1"))

    def test_ip_range_generation(self):
        ips = get_ip_range_from_bounds("192.168.1.1", "192.168.1.5")
        self.assertEqual(len(ips), 5)
        self.assertEqual(ips[0], "192.168.1.1")
        self.assertEqual(ips[-1], "192.168.1.5")

    def test_subnet_range(self):
        ips = get_ip_range("192.168.1.0/30")
        # /30 has 2 usable hosts
        self.assertEqual(len(ips), 2)
        self.assertIn("192.168.1.1", ips)
        self.assertIn("192.168.1.2", ips)


class TestPrivateIP(unittest.TestCase):
    """Test private IP detection."""

    def test_private_ips(self):
        self.assertTrue(is_private_ip("192.168.1.1"))
        self.assertTrue(is_private_ip("10.0.0.1"))
        self.assertTrue(is_private_ip("172.16.0.1"))

    def test_public_ips(self):
        self.assertFalse(is_private_ip("8.8.8.8"))
        self.assertFalse(is_private_ip("1.1.1.1"))

    def test_invalid_ips(self):
        self.assertFalse(is_private_ip("invalid"))


class TestSubnetInfo(unittest.TestCase):
    """Test subnet information calculation."""

    def test_subnet_info(self):
        info = get_subnet_info("192.168.1.100", "255.255.255.0")
        self.assertEqual(info['network'], "192.168.1.0")
        self.assertEqual(info['broadcast'], "192.168.1.255")
        self.assertEqual(info['cidr'], "192.168.1.0/24")
        self.assertEqual(info['prefix_len'], "24")
        self.assertEqual(info['gateway'], "192.168.1.1")


class TestFormatBytes(unittest.TestCase):
    """Test byte formatting."""

    def test_bytes(self):
        self.assertEqual(format_bytes(0), "0 B")
        self.assertEqual(format_bytes(100), "100 B")

    def test_kilobytes(self):
        self.assertEqual(format_bytes(1024), "1.0 KB")
        self.assertEqual(format_bytes(1536), "1.5 KB")

    def test_megabytes(self):
        self.assertEqual(format_bytes(1048576), "1.0 MB")

    def test_gigabytes(self):
        self.assertEqual(format_bytes(1073741824), "1.0 GB")

    def test_negative(self):
        self.assertEqual(format_bytes(-1), "0 B")


class TestFormatSpeed(unittest.TestCase):
    """Test speed formatting."""

    def test_speeds(self):
        self.assertEqual(format_speed(0), "0 B/s")
        self.assertEqual(format_speed(1024), "1.0 KB/s")
        self.assertEqual(format_speed(1048576), "1.0 MB/s")


class TestFormatDuration(unittest.TestCase):
    """Test duration formatting."""

    def test_durations(self):
        self.assertEqual(format_duration(0.5), "500ms")
        self.assertEqual(format_duration(5.5), "5.5s")
        self.assertEqual(format_duration(90), "1m 30s")
        self.assertEqual(format_duration(3661), "1h 1m")

    def test_negative(self):
        self.assertEqual(format_duration(-1), "0s")


class TestFormatPing(unittest.TestCase):
    """Test ping formatting."""

    def test_pings(self):
        self.assertEqual(format_ping(None), "-")
        self.assertEqual(format_ping(0.5), "<1ms")
        self.assertEqual(format_ping(5.0), "5ms")
        self.assertEqual(format_ping(123.456), "123ms")


class TestSanitizeInput(unittest.TestCase):
    """Test input sanitization."""

    def test_normal_input(self):
        self.assertEqual(sanitize_input("Hello"), "Hello")

    def test_whitespace(self):
        self.assertEqual(sanitize_input("  Hello  "), "Hello")

    def test_max_length(self):
        long_text = "a" * 1000
        result = sanitize_input(long_text, max_length=100)
        self.assertEqual(len(result), 100)

    def test_empty(self):
        self.assertEqual(sanitize_input(""), "")
        self.assertEqual(sanitize_input(None), "")


class TestParseIPPort(unittest.TestCase):
    """Test IP:port parsing."""

    def test_valid(self):
        result = parse_ip_port("192.168.1.1:5000")
        self.assertEqual(result, ("192.168.1.1", 5000))

    def test_invalid(self):
        self.assertIsNone(parse_ip_port(""))
        self.assertIsNone(parse_ip_port("192.168.1.1"))
        self.assertIsNone(parse_ip_port("invalid:port"))


class TestTruncateString(unittest.TestCase):
    """Test string truncation."""

    def test_short_string(self):
        self.assertEqual(truncate_string("Hello", 10), "Hello")

    def test_long_string(self):
        result = truncate_string("Hello, World!", 10)
        self.assertEqual(len(result), 10)
        self.assertTrue(result.endswith("..."))


class TestLocalIP(unittest.TestCase):
    """Test local IP detection."""

    def test_get_local_ip(self):
        ip = get_local_ip()
        self.assertTrue(validate_ip(ip))


if __name__ == "__main__":
    unittest.main()
