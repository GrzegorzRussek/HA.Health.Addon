"""Medication sensors for Health Addon."""
import logging
from datetime import datetime, timedelta
from typing import Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_utils

from ..utils.database import Database

_LOGGER = logging.getLogger(__name__)


class MedicationSensor(SensorEntity):
    """Sensor for medication inventory and intake."""

    def __init__(self, database: Database, user_id: str, medication_id: int, name: str, dosage: str):
        self._database = database
        self._user_id = user_id
        self._medication_id = medication_id
        self._name = name
        self._dosage = dosage
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}

    @property
    def name(self) -> str:
        return f"Medication {self._name}"

    @property
    def unique_id(self) -> str:
        return f"health_addon_medication_{self._user_id}_{self._medication_id}"

    @property
    def native_unit_of_measurement(self) -> str:
        return "dose"

    @property
    def icon(self) -> str:
        return "mdi:pill"

    async def async_update(self) -> None:
        """Update sensor state."""
        try:
            # Get medication details
            meds = await self._database.get_medications(self._user_id)
            med = next((m for m in meds if m["id"] == self._medication_id), None)
            
            if med:
                self._attr_native_value = med["quantity"]
                self._attr_extra_state_attributes = {
                    "dosage": self._dosage,
                    "barcode": med.get("barcode"),
                    "expiration_date": med.get("expiration_date"),
                    "user_id": self._user_id,
                }
                
                # Check last dose
                last_dose = await self._database.get_last_dose(self._user_id, self._medication_id)
                if last_dose:
                    self._attr_extra_state_attributes["last_taken_at"] = last_dose.isoformat()
                    hours_since = (datetime.now() - last_dose).total_seconds() / 3600
                    self._attr_extra_state_attributes["hours_since_last_dose"] = round(hours_since, 1)
                    
                    # Get recent logs
                    logs = await self._database.get_medication_logs(self._user_id, self._medication_id, limit=10)
                    self._attr_extra_state_attributes["recent_logs"] = logs
        except Exception as e:
            _LOGGER.error("Error updating medication sensor %s: %s", self._name, e)

    async def log_dose(self) -> None:
        """Log that a dose was taken."""
        await self._database.log_medication_taken(self._user_id, self._medication_id)
        await self.async_update()
