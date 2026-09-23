"""Network utility functions for interface detection and IP operations."""
import socket
import platform
import ipaddress
import logging
import subprocess
import re
from typing import List, Optional, Tuple, Dict

import psutil

logger = logging.getLogger(__name__)


def get_local_ip() -> str:
    """Get the primary local IP address.

    Returns:
        Local IP address string.
    """
    try:
        # Create a UDP socket that doesn't actually send data
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            return "127.0.0.1"


def get_network_interfaces() -> List[Dict[str, str]]:
    """Get all network interface information.

    Returns:
        List of dicts with interface details.
    """
    interfaces = []
    try:
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()

        for name, addr_list in addrs.items():
            iface_info = {
                'name': name,
                'ipv4': '',
                'netmask': '',
                'mac': '',
                'is_up': False,
                'speed': 0,
            }

            # Get link status
            if name in stats:
                iface_info['is_up'] = stats[name].isup
                iface_info['speed'] = stats[name].speed

            for addr in addr_list:
                if addr.family == socket.AF_INET:
                    iface_info['ipv4'] = addr.address
                    iface_info['netmask'] = addr.netmask or ''
                elif addr.family == psutil.AF_LINK:
                    iface_info['mac'] = addr.address

            # Only include interfaces with an IPv4 address
            if iface_info['ipv4'] and iface_info['ipv4'] != '127.0.0.1':
                interfaces.append(iface_info)

    except Exception as e:
        logger.error("Error getting network interfaces: %s", e)

    return interfaces


def get_active_interface() -> Optional[Dict[str, str]]:
    """Get the currently active network interface.

    Returns:
        Dict with interface details or None.
    """
    local_ip = get_local_ip()
    interfaces = get_network_interfaces()

    for iface in interfaces:
        if iface['ipv4'] == local_ip:
            return iface

    # Return first up interface if exact match not found
    for iface in interfaces:
        if iface['is_up']:
            return iface

    return interfaces[0] if interfaces else None


def get_subnet_info(ip: str, netmask: str) -> Dict[str, str]:
    """Calculate subnet information from IP and netmask.

    Args:
        ip: IPv4 address.
        netmask: Subnet mask.

    Returns:
        Dict with network, broadcast, cidr, gateway (guessed).
    """
    try:
        interface = ipaddress.IPv4Interface(f"{ip}/{netmask}")
        network = interface.network

        # Get first usable host without materializing all hosts
        first_host = next(network.hosts(), None)
        gateway = str(first_host) if first_host else str(network.network_address)

        return {
            'network': str(network.network_address),
            'broadcast': str(network.broadcast_address),
            'cidr': str(network),
            'prefix_len': str(network.prefixlen),
            'gateway': gateway,
            'total_hosts': str(network.num_addresses - 2),  # Exclude network/broadcast
        }
    except (ipaddress.AddressValueError, ValueError) as e:
        logger.error("Error calculating subnet: %s", e)
        return {
            'network': 'N/A', 'broadcast': 'N/A', 'cidr': 'N/A',
            'prefix_len': 'N/A', 'gateway': 'N/A', 'total_hosts': '0',
        }


def get_ip_range(subnet: str) -> List[str]:
    """Get all host IPs in a subnet.

    Args:
        subnet: Subnet in CIDR notation (e.g., '192.168.1.0/24').

    Returns:
        List of IP address strings.
    """
    try:
        network = ipaddress.IPv4Network(subnet, strict=False)
        return [str(host) for host in network.hosts()]
    except (ipaddress.AddressValueError, ValueError) as e:
        logger.error("Error getting IP range: %s", e)
        return []


def get_ip_range_from_bounds(start_ip: str, end_ip: str) -> List[str]:
    """Get all IPs between start and end (inclusive).

    Args:
        start_ip: Starting IP address.
        end_ip: Ending IP address.

    Returns:
        List of IP address strings.
    """
    try:
        start = int(ipaddress.IPv4Address(start_ip))
        end = int(ipaddress.IPv4Address(end_ip))
        return [str(ipaddress.IPv4Address(ip)) for ip in range(start, end + 1)]
    except (ipaddress.AddressValueError, ValueError) as e:
        logger.error("Error generating IP range: %s", e)
        return []


def get_default_gateway() -> str:
    """Get the default gateway IP.

    Returns:
        Gateway IP string or 'N/A'.
    """
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["ipconfig"], capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.split('\n'):
                if 'Default Gateway' in line or 'Gateway' in line:
                    match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                    if match:
                        return match.group(1)
        else:
            result = subprocess.run(
                ["ip", "route", "show", "default"],
                capture_output=True, text=True, timeout=5
            )
            match = re.search(r'via\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
            if match:
                return match.group(1)
    except Exception as e:
        logger.error("Error getting default gateway: %s", e)

    # Fallback: guess from local IP
    local_ip = get_local_ip()
    parts = local_ip.rsplit('.', 1)
    if len(parts) == 2:
        return f"{parts[0]}.1"
    return "N/A"


def resolve_hostname(ip: str) -> str:
    """Resolve hostname for an IP address.

    Args:
        ip: IP address to resolve.

    Returns:
        Hostname or empty string.
    """
    try:
        hostname = socket.getfqdn(ip)
        # getfqdn returns the IP itself if it can't resolve
        if hostname == ip:
            hostname = socket.gethostbyaddr(ip)[0]
        return hostname
    except (socket.herror, socket.gaierror, OSError):
        return ""


def get_mac_address(ip: str) -> str:
    """Get MAC address for an IP using ARP table.

    Args:
        ip: Target IP address.

    Returns:
        MAC address string or empty string.
    """
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["arp", "-a", ip],
                capture_output=True, text=True, timeout=5
            )
            # Parse Windows ARP output
            for line in result.stdout.split('\n'):
                if ip in line:
                    match = re.search(
                        r'([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}', line
                    )
                    if match:
                        return match.group(0).upper().replace('-', ':')
        else:
            result = subprocess.run(
                ["arp", "-n", ip],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.split('\n'):
                if ip in line:
                    match = re.search(
                        r'([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}', line
                    )
                    if match:
                        return match.group(0).upper()
    except Exception as e:
        logger.debug("Could not get MAC for %s: %s", ip, e)

    return ""


def get_hostname() -> str:
    """Get the local machine's hostname.

    Returns:
        Local hostname.
    """
    try:
        return socket.gethostname()
    except Exception:
        return "Unknown"
