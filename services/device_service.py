"""Device management service."""
import logging
from typing import List, Optional

from database.database import DatabaseManager
from database.repository import DeviceRepository
from database.models import Device

logger = logging.getLogger(__name__)


class DeviceService:
    """Business logic for device management."""

    def __init__(self, db: DatabaseManager):
        self.repo = DeviceRepository(db)

    def save_device(self, device: Device) -> int:
        """Save or update a discovered device.

        Args:
            device: Device to save.

        Returns:
            Row ID.
        """
        device_id = self.repo.upsert(device)
        logger.info("Device saved: %s (%s) - %s",
                     device.ip_address, device.hostname, device.status)
        return device_id

    def save_devices(self, devices: List[Device]) -> None:
        """Save multiple devices from a scan using batch upsert.

        Args:
            devices: List of Device objects.
        """
        if not devices:
            return

        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        query = """INSERT INTO devices (ip_address, hostname, mac_address, status,
                       response_time, last_seen, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(ip_address) DO UPDATE SET
                       hostname = excluded.hostname,
                       mac_address = CASE WHEN excluded.mac_address != '' 
                           THEN excluded.mac_address ELSE devices.mac_address END,
                       status = excluded.status,
                       response_time = excluded.response_time,
                       last_seen = excluded.last_seen,
                       notes = CASE WHEN excluded.notes != '' 
                           THEN excluded.notes ELSE devices.notes END
                """

        params_list = [
            (d.ip_address, d.hostname, d.mac_address,
             d.status, d.response_time, now, d.notes)
            for d in devices
        ]

        try:
            self.repo.db.execute_many(query, params_list)
            logger.info("Batch saved %d devices", len(devices))
        except Exception as e:
            logger.error("Error batch saving devices: %s", e)
            # Fallback to individual upserts
            for device in devices:
                try:
                    self.repo.upsert(device)
                except Exception as err:
                    logger.error("Error saving device %s: %s",
                                 device.ip_address, err)

    def get_all_devices(self) -> List[Device]:
        """Get all known devices."""
        return self.repo.get_all()

    def get_online_devices(self) -> List[Device]:
        """Get all online devices."""
        return self.repo.get_by_status("ONLINE")

    def get_offline_devices(self) -> List[Device]:
        """Get all offline devices."""
        return self.repo.get_by_status("OFFLINE")

    def get_device(self, ip: str) -> Optional[Device]:
        """Get a device by IP."""
        return self.repo.get_by_ip(ip)

    def get_statistics(self) -> dict:
        """Get device statistics.

        Returns:
            Dict with total, online, offline counts.
        """
        return {
            'total': self.repo.count(),
            'online': self.repo.count("ONLINE"),
            'offline': self.repo.count("OFFLINE"),
        }

    def delete_device(self, ip: str) -> None:
        """Delete a device."""
        self.repo.delete(ip)
        logger.info("Device deleted: %s", ip)

    def mark_all_offline(self) -> None:
        """Mark all devices as offline (e.g., before a new scan)."""
        self.repo.set_all_offline()

    def update_notes(self, ip: str, notes: str) -> None:
        """Update notes for a device."""
        self.repo.update_notes(ip, notes)
