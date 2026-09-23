"""LAN Scanner using concurrent ping operations."""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

from PySide6.QtCore import QThread, Signal

from network.ping import ping_host
from network.network_utils import (
    resolve_hostname, get_mac_address,
    get_ip_range, get_ip_range_from_bounds,
    get_active_interface, get_subnet_info
)
from database.models import Device

logger = logging.getLogger(__name__)


class LANScanner(QThread):
    """Scans LAN for active devices using concurrent ping.

    Signals:
        device_found: Emitted when a device responds to ping.
        scan_progress: Emitted with (current, total) progress.
        scan_complete: Emitted with list of all discovered devices.
        scan_error: Emitted with error message string.
        scan_status: Emitted with status message string.
    """

    device_found = Signal(object)    # Device
    scan_progress = Signal(int, int)  # current, total
    scan_complete = Signal(list)      # List[Device]
    scan_error = Signal(str)          # error message
    scan_status = Signal(str)         # status message

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stop_flag = False
        self._ip_list: List[str] = []
        self._timeout: float = 1.0
        self._thread_count: int = 50

    def configure(self, ip_list: Optional[List[str]] = None,
                  subnet: Optional[str] = None,
                  start_ip: Optional[str] = None,
                  end_ip: Optional[str] = None,
                  timeout: float = 1.0,
                  thread_count: int = 50) -> None:
        """Configure scan parameters.

        Args:
            ip_list: Explicit list of IPs to scan.
            subnet: Subnet in CIDR notation.
            start_ip: Start of IP range.
            end_ip: End of IP range.
            timeout: Ping timeout in seconds.
            thread_count: Number of concurrent threads.
        """
        self._timeout = timeout
        self._thread_count = thread_count

        if ip_list:
            self._ip_list = ip_list
        elif subnet:
            self._ip_list = get_ip_range(subnet)
        elif start_ip and end_ip:
            self._ip_list = get_ip_range_from_bounds(start_ip, end_ip)
        else:
            # Auto-detect subnet
            iface = get_active_interface()
            if iface and iface['ipv4'] and iface['netmask']:
                info = get_subnet_info(iface['ipv4'], iface['netmask'])
                self._ip_list = get_ip_range(info['cidr'])
            else:
                self._ip_list = []

    def stop(self) -> None:
        """Request the scan to stop."""
        self._stop_flag = True
        logger.info("Scan stop requested")

    def run(self) -> None:
        """Execute the LAN scan in a background thread."""
        self._stop_flag = False
        discovered: List[Device] = []

        if not self._ip_list:
            self.scan_error.emit("No IP addresses to scan. Check network configuration.")
            return

        total = len(self._ip_list)
        self.scan_status.emit(f"Scanning {total} addresses...")
        logger.info("Starting LAN scan: %d addresses, timeout=%.1fs, threads=%d",
                     total, self._timeout, self._thread_count)

        completed = 0

        try:
            with ThreadPoolExecutor(max_workers=self._thread_count) as executor:
                future_to_ip = {
                    executor.submit(self._scan_host, ip): ip
                    for ip in self._ip_list
                }

                for future in as_completed(future_to_ip):
                    if self._stop_flag:
                        executor.shutdown(wait=False, cancel_futures=True)
                        self.scan_status.emit("Scan cancelled")
                        logger.info("Scan cancelled by user")
                        break

                    completed += 1
                    self.scan_progress.emit(completed, total)

                    try:
                        device = future.result()
                        if device and device.is_online:
                            discovered.append(device)
                            self.device_found.emit(device)
                    except Exception as e:
                        logger.debug("Scan error for an IP: %s", e)

        except Exception as e:
            self.scan_error.emit(f"Scan failed: {str(e)}")
            logger.error("Scan failed: %s", e)
            return

        if not self._stop_flag:
            self.scan_status.emit(
                f"Scan complete. Found {len(discovered)} device(s) online."
            )
            logger.info("Scan complete: %d/%d devices online", len(discovered), total)

        self.scan_complete.emit(discovered)

    def _scan_host(self, ip: str) -> Device:
        """Scan a single host.

        Args:
            ip: IP address to scan.

        Returns:
            Device with scan results.
        """
        device = Device(ip_address=ip)

        response_time = ping_host(ip, timeout=self._timeout)

        if response_time is not None:
            device.status = "ONLINE"
            device.response_time = response_time

            # Resolve hostname (function handles exceptions internally)
            device.hostname = resolve_hostname(ip)

            # Get MAC address (function handles exceptions internally)
            device.mac_address = get_mac_address(ip)

            logger.debug("Host found: %s (%s) - %.1fms",
                         ip, device.hostname or "unknown", response_time)
        else:
            device.status = "OFFLINE"

        return device
