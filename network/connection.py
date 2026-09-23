"""Connection monitor using psutil for active network connections."""
import socket
import logging
from typing import List, Optional

import psutil

from database.models import Connection

logger = logging.getLogger(__name__)


class ConnectionMonitor:
    """Monitors active network connections using psutil."""

    # Map psutil connection status to readable names
    STATUS_MAP = {
        'ESTABLISHED': 'ESTABLISHED',
        'SYN_SENT': 'SYN_SENT',
        'SYN_RECV': 'SYN_RECEIVED',
        'FIN_WAIT1': 'FIN_WAIT_1',
        'FIN_WAIT2': 'FIN_WAIT_2',
        'TIME_WAIT': 'TIME_WAIT',
        'CLOSE': 'CLOSED',
        'CLOSE_WAIT': 'CLOSE_WAIT',
        'LAST_ACK': 'LAST_ACK',
        'LISTEN': 'LISTEN',
        'CLOSING': 'CLOSING',
        'NONE': 'NONE',
    }

    @staticmethod
    def get_connections(protocol: Optional[str] = None) -> List[Connection]:
        """Get active network connections.

        Args:
            protocol: Filter by 'TCP', 'UDP', or None for all.

        Returns:
            List of Connection objects.
        """
        connections = []
        try:
            if protocol == "TCP":
                kind = 'tcp'
            elif protocol == "UDP":
                kind = 'udp'
            else:
                kind = 'inet'

            for conn in psutil.net_connections(kind=kind):
                try:
                    local_addr = conn.laddr.ip if conn.laddr else ""
                    local_port = conn.laddr.port if conn.laddr else 0
                    remote_addr = conn.raddr.ip if conn.raddr else ""
                    remote_port = conn.raddr.port if conn.raddr else 0

                    # Determine protocol
                    proto = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"

                    # Get status
                    status = ConnectionMonitor.STATUS_MAP.get(
                        conn.status, conn.status
                    )

                    # Get process name
                    process_name = ""
                    if conn.pid:
                        try:
                            proc = psutil.Process(conn.pid)
                            process_name = proc.name()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            process_name = "N/A"

                    connections.append(Connection(
                        local_address=local_addr,
                        local_port=local_port,
                        remote_address=remote_addr,
                        remote_port=remote_port,
                        protocol=proto,
                        state=status,
                        pid=conn.pid,
                        process_name=process_name,
                    ))
                except Exception as e:
                    logger.debug("Error parsing connection: %s", e)
                    continue

        except psutil.AccessDenied:
            logger.warning("Access denied for net_connections. Run as administrator.")
        except Exception as e:
            logger.error("Error getting connections: %s", e)

        return connections

    @staticmethod
    def count_connections() -> dict:
        """Count connections by protocol and state.

        Returns:
            Dict with counts: total, tcp, udp, established, listening.
        """
        counts = {
            'total': 0,
            'tcp': 0,
            'udp': 0,
            'established': 0,
            'listening': 0,
        }

        try:
            for conn in psutil.net_connections(kind='inet'):
                counts['total'] += 1
                if conn.type == socket.SOCK_STREAM:  # TCP
                    counts['tcp'] += 1
                else:
                    counts['udp'] += 1

                if conn.status == 'ESTABLISHED':
                    counts['established'] += 1
                elif conn.status == 'LISTEN':
                    counts['listening'] += 1

        except (psutil.AccessDenied, Exception) as e:
            logger.debug("Error counting connections: %s", e)

        return counts
