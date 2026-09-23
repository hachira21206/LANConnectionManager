"""Helper utility functions for formatting and conversions."""
from datetime import datetime, timedelta
from typing import Optional


def format_bytes(bytes_value: int) -> str:
    """Format bytes into human-readable string.

    Args:
        bytes_value: Number of bytes.

    Returns:
        Formatted string (e.g., '1.5 MB').
    """
    if bytes_value < 0:
        return "0 B"
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    value = float(bytes_value)
    while value >= 1024 and unit_index < len(units) - 1:
        value /= 1024
        unit_index += 1
    if unit_index == 0:
        return f"{int(value)} {units[unit_index]}"
    return f"{value:.1f} {units[unit_index]}"


def format_speed(bytes_per_sec: float) -> str:
    """Format speed into human-readable string.

    Args:
        bytes_per_sec: Speed in bytes per second.

    Returns:
        Formatted speed string (e.g., '12.5 MB/s').
    """
    if bytes_per_sec < 0:
        return "0 B/s"
    units = ['B/s', 'KB/s', 'MB/s', 'GB/s']
    unit_index = 0
    value = float(bytes_per_sec)
    while value >= 1024 and unit_index < len(units) - 1:
        value /= 1024
        unit_index += 1
    if unit_index == 0:
        return f"{int(value)} {units[unit_index]}"
    return f"{value:.1f} {units[unit_index]}"


def format_duration(seconds: float) -> str:
    """Format duration into human-readable string.

    Args:
        seconds: Duration in seconds.

    Returns:
        Formatted duration (e.g., '2m 15s').
    """
    if seconds < 0:
        return "0s"
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    if seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}h {minutes}m"


def format_ping(ms: Optional[float]) -> str:
    """Format ping response time.

    Args:
        ms: Ping time in milliseconds, or None.

    Returns:
        Formatted ping string.
    """
    if ms is None:
        return "-"
    if ms < 1:
        return "<1ms"
    return f"{ms:.0f}ms"


def get_timestamp() -> str:
    """Get current timestamp string.

    Returns:
        Formatted timestamp.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def time_ago(timestamp_str: str) -> str:
    """Get human-readable time ago string.

    Args:
        timestamp_str: Timestamp in '%Y-%m-%d %H:%M:%S' format.

    Returns:
        Human-readable time difference.
    """
    try:
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        diff = datetime.now() - timestamp
        if diff.total_seconds() < 60:
            return "Just now"
        if diff.total_seconds() < 3600:
            return f"{int(diff.total_seconds() // 60)}m ago"
        if diff.total_seconds() < 86400:
            return f"{int(diff.total_seconds() // 3600)}h ago"
        return f"{diff.days}d ago"
    except (ValueError, TypeError):
        return "Unknown"


def truncate_string(text: str, max_length: int = 30) -> str:
    """Truncate string with ellipsis.

    Args:
        text: Input string.
        max_length: Maximum length.

    Returns:
        Truncated string.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
