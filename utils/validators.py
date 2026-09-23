"""Input validation utilities for network parameters."""
import ipaddress
import re
from typing import Optional, Tuple

# Pre-compiled regex patterns
_HOSTNAME_RE = re.compile(
    r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?'
    r'(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
)
_CONTROL_CHAR_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')


def validate_ip(ip: str) -> bool:
    """Validate an IPv4 address.

    Args:
        ip: IP address string.

    Returns:
        True if valid IPv4 address.
    """
    try:
        ipaddress.IPv4Address(ip)
        return True
    except (ipaddress.AddressValueError, ValueError):
        return False


def validate_port(port) -> bool:
    """Validate a port number.

    Args:
        port: Port number (int or string).

    Returns:
        True if valid port (1-65535).
    """
    try:
        port_int = int(port)
        return 1 <= port_int <= 65535
    except (ValueError, TypeError):
        return False


def validate_subnet(subnet: str) -> bool:
    """Validate a subnet in CIDR notation.

    Args:
        subnet: Subnet string (e.g., '192.168.1.0/24').

    Returns:
        True if valid subnet.
    """
    if not subnet or '/' not in subnet:
        return False
    try:
        ipaddress.IPv4Network(subnet, strict=False)
        return True
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError, ValueError):
        return False


def validate_ip_range(start_ip: str, end_ip: str) -> bool:
    """Validate an IP range.

    Args:
        start_ip: Start of range.
        end_ip: End of range.

    Returns:
        True if valid range (start <= end).
    """
    try:
        start = ipaddress.IPv4Address(start_ip)
        end = ipaddress.IPv4Address(end_ip)
        return start <= end
    except (ipaddress.AddressValueError, ValueError):
        return False


def is_private_ip(ip: str) -> bool:
    """Check if an IP address is private (LAN).

    Args:
        ip: IP address string.

    Returns:
        True if private/LAN address.
    """
    try:
        addr = ipaddress.IPv4Address(ip)
        return addr.is_private
    except (ipaddress.AddressValueError, ValueError):
        return False


def validate_hostname(hostname: str) -> bool:
    """Validate a hostname.

    Args:
        hostname: Hostname string.

    Returns:
        True if valid hostname.
    """
    if not hostname or len(hostname) > 253:
        return False
    return bool(_HOSTNAME_RE.match(hostname))


def sanitize_input(text: str, max_length: int = 500) -> str:
    """Sanitize user input text.

    Args:
        text: Raw input text.
        max_length: Maximum allowed length.

    Returns:
        Sanitized text.
    """
    if not text:
        return ""
    # Strip whitespace and limit length
    text = text.strip()[:max_length]
    # Remove null bytes and control characters (keep newlines, tabs)
    text = _CONTROL_CHAR_RE.sub('', text)
    return text


def parse_ip_port(address: str) -> Optional[Tuple[str, int]]:
    """Parse an 'IP:port' string.

    Args:
        address: String in format 'IP:port'.

    Returns:
        Tuple of (ip, port) or None if invalid.
    """
    try:
        parts = address.rsplit(':', 1)
        if len(parts) != 2:
            return None
        ip, port_str = parts
        if validate_ip(ip) and validate_port(port_str):
            return (ip, int(port_str))
        return None
    except (ValueError, IndexError):
        return None
