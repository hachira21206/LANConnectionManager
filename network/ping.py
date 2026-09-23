"""Ping utility using system ping command."""
import subprocess
import platform
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def ping_host(ip: str, timeout: float = 1.0, count: int = 1) -> Optional[float]:
    """Ping a host and return response time in milliseconds.

    Args:
        ip: Target IP address.
        timeout: Timeout in seconds.
        count: Number of ping packets.

    Returns:
        Response time in ms, or None if host is unreachable.
    """
    try:
        system = platform.system().lower()

        if system == "windows":
            cmd = [
                "ping", "-n", str(count),
                "-w", str(int(timeout * 1000)),
                ip
            ]
        else:
            cmd = [
                "ping", "-c", str(count),
                "-W", str(int(timeout)),
                ip
            ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 2,  # Extra margin
            creationflags=subprocess.CREATE_NO_WINDOW if system == "windows" else 0
        )

        if result.returncode == 0:
            return _parse_ping_time(result.stdout, system)

        return None

    except subprocess.TimeoutExpired:
        logger.debug("Ping timeout for %s", ip)
        return None
    except FileNotFoundError:
        logger.error("Ping command not found")
        return None
    except Exception as e:
        logger.debug("Ping error for %s: %s", ip, e)
        return None


def _parse_ping_time(output: str, system: str) -> Optional[float]:
    """Parse ping response time from output.

    Args:
        output: Ping command stdout.
        system: Operating system name.

    Returns:
        Response time in ms or None.
    """
    try:
        if system == "windows":
            # Windows: "Reply from x.x.x.x: bytes=32 time=2ms TTL=64"
            # Or with "<1ms"
            match = re.search(r'time[=<](\d+\.?\d*)ms', output, re.IGNORECASE)
            if match:
                return float(match.group(1))
            # Check for <1ms case
            if 'time<1ms' in output.lower():
                return 0.5
        else:
            # Linux/Mac: "64 bytes from x.x.x.x: icmp_seq=1 ttl=64 time=2.05 ms"
            match = re.search(r'time=(\d+\.?\d*)\s*ms', output)
            if match:
                return float(match.group(1))
    except (ValueError, AttributeError):
        pass

    return None


def is_host_reachable(ip: str, timeout: float = 1.0) -> bool:
    """Check if a host is reachable via ping.

    Args:
        ip: Target IP address.
        timeout: Timeout in seconds.

    Returns:
        True if host responds to ping.
    """
    return ping_host(ip, timeout) is not None
