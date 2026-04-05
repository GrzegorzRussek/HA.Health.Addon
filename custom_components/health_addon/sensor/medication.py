"""Medication sensors for Health Addon."""
import json
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


def parse_schedule(schedule_str: str) -> list[datetime]:
    """Parse schedule string to list of times."""
    if not schedule_str:
        return []
    try:
        times = json.loads(schedule_str)
        result = []
        now = datetime.now()
        for time_str in times:
            # Parse HH:MM format
            hour, minute = map(int, time_str.split(":"))
            dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            # If time has passed today, schedule for tomorrow
            if dt <= now:
                dt += timedelta(days=1)
            result.append(dt)
        return sorted(result)
    except:
        return []


class MedicationSensor(SensorEntity):
    """Sensor for medication inventory and intake."""

    def __init__(self, database: Database, user_id: str, medication_id: int, name: str, dosage: str):
        self._database = database
        self._user_id = user_id
        self._medication_id = medication_id
        self._name = name
        self._dosage = dosage
        self._schedule = None
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
                self._schedule = med.get("schedule")
                self._attr_extra_state_attributes = {
                    "dosage": self._dosage,
                    "barcode": med.get("barcode"),
                    "expiration_date": med.get("expiration_date"),
                    "user_id": self._user_id,
                    "schedule": self._schedule,
                }
                
                # Parse schedule and calculate next dose
                if self._schedule:
                    schedule_times = parse_schedule(self._schedule)
                    if schedule_times:
                        next_dose = schedule_times[0]
                        self._attr_extra_state_attributes["next_dose_at"] = next_dose.isoformat()
                        self._attr_extra_state_attributes["schedule_times"] = [dt.isoformat() for dt in schedule_times]
                
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
