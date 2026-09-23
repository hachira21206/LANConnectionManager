"""Real-time network traffic monitor using psutil."""
import time
import logging
from typing import Optional, Dict, List
from collections import deque

import psutil
from PySide6.QtCore import QThread, Signal 
from database.models import TrafficStats

logger = logging.getLogger(__name__)


class TrafficMonitor(QThread):
    """Monitors network traffic in real-time.

    Signals:
        stats_updated: (stats: TrafficStats)
        monitor_error: (error: str)
    """

    stats_updated = Signal(object)  # TrafficStats
    monitor_error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running: bool = False
        self._paused: bool = False
        self._interval: float = 1.0
        self._interface: Optional[str] = None
        self._prev_interface: Optional[str] = None  # Track interface changes
        self._history: deque = deque(maxlen=120)  # 2 minutes of data

    def configure(self, interval: float = 1.0,
                  interface: Optional[str] = None) -> None:
        """Configure the traffic monitor.

        Args:
            interval: Polling interval in seconds.
            interface: Network interface name, or None for all.
        """
        self._interval = max(0.5, interval)
        self._interface = interface

    def set_interface(self, interface: Optional[str]) -> None:
        """Change the monitored interface."""
        self._interface = interface

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def history(self) -> List[TrafficStats]:
        return list(self._history)

    def pause(self) -> None:
        """Pause monitoring."""
        self._paused = True

    def resume(self) -> None:
        """Resume monitoring."""
        self._paused = False

    def clear_history(self) -> None:
        """Clear stored history data."""
        self._history.clear()

    def stop(self) -> None:
        """Stop the monitor."""
        self._running = False

    def _interruptible_sleep(self, seconds: float) -> None:
        """Sleep in small increments so the thread can exit quickly."""
        elapsed = 0.0
        step = 0.1
        while elapsed < seconds and self._running:
            time.sleep(step)
            elapsed += step

    def run(self) -> None:
        """Main monitoring loop."""
        self._running = True
        prev_counters = None
        prev_time = None

        logger.info("Traffic monitor started (interface=%s, interval=%.1fs)",
                     self._interface or "all", self._interval)

        try:
            while self._running:
                if self._paused:
                    self._interruptible_sleep(self._interval)
                    continue

                try:
                    # Detect interface change and reset baseline
                    if self._interface != self._prev_interface:
                        prev_counters = None
                        prev_time = None
                        self._prev_interface = self._interface

                    # Get current counters
                    if self._interface:
                        counters_dict = psutil.net_io_counters(pernic=True)
                        if self._interface in counters_dict:
                            counters = counters_dict[self._interface]
                        else:
                            counters = psutil.net_io_counters()
                    else:
                        counters = psutil.net_io_counters()

                    current_time = time.time()

                    if prev_counters and prev_time:
                        dt = current_time - prev_time
                        if dt > 0:
                            # Guard against negative speed from counter
                            # resets (OS restart, driver reload, etc.)
                            dl_delta = counters.bytes_recv - prev_counters.bytes_recv
                            ul_delta = counters.bytes_sent - prev_counters.bytes_sent

                            download_speed = max(0.0, dl_delta / dt)
                            upload_speed = max(0.0, ul_delta / dt)

                            stats = TrafficStats(
                                bytes_sent=counters.bytes_sent,
                                bytes_recv=counters.bytes_recv,
                                packets_sent=counters.packets_sent,
                                packets_recv=counters.packets_recv,
                                download_speed=download_speed,
                                upload_speed=upload_speed,
                                timestamp=current_time,
                            )
                            self._history.append(stats)
                            self.stats_updated.emit(stats)

                    prev_counters = counters
                    prev_time = current_time

                except Exception as e:
                    self.monitor_error.emit(f"Monitor error: {str(e)}")
                    logger.error("Traffic monitor error: %s", e)

                self._interruptible_sleep(self._interval)

        finally:
            self._running = False
            logger.info("Traffic monitor stopped")

    @staticmethod
    def get_available_interfaces() -> List[str]:
        """Get list of available network interfaces.

        Returns:
            List of interface names.
        """
        try:
            stats = psutil.net_if_stats()
            return [name for name, s in stats.items() if s.isup]
        except Exception:
            return []

