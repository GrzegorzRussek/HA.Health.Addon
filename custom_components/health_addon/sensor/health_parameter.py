"""Health parameter sensors for Health Addon."""
import logging
from datetime import datetime
from typing import Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ..utils.database import Database

_LOGGER = logging.getLogger(__name__)

PARAMS = ["pressure_systolic", "pressure_diastolic", "blood_sugar", "heart_rate", "temperature", "weight", "oxygen"]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up health parameter sensors."""
    db: Database = hass.data["health_addon"]["database"]
    user_id = config_entry.data.get("user_id")
    
    entities = []
    for param in PARAMS:
        entities.append(HealthParameterSensor(db, user_id, param))
    
    async_add_entities(entities)


class HealthParameterSensor(SensorEntity):
    """Sensor for health parameters."""

    def __init__(self, database: Database, user_id: str, parameter_name: str):
        self._database = database
        self._user_id = user_id
        self._parameter_name = parameter_name
        self._attr_extra_state_attributes = {}
        self._attr_native_value = None
        self._attr_native_unit = None

    @property
    def name(self) -> str:
        return f"Health {self._parameter_name.replace('_', ' ').title()}"

    @property
    def unique_id(self) -> str:
        return f"health_addon_{self._user_id}_{self._parameter_name}"

    @property
    def native_value(self):
        return self._attr_native_value

    @property
    def native_unit_of_measurement(self):
        return self._attr_native_unit

    @property
    def icon(self) -> str:
        icons = {
            "pressure_systolic": "mdi:heart-pulse",
            "pressure_diastolic": "mdi:heart-pulse",
            "blood_sugar": "mdi:blood-bag",
            "heart_rate": "mdi:heart",
            "temperature": "mdi:thermometer",
            "weight": "mdi:scale",
            "oxygen": "mdi:lungs",
        }
        return icons.get(self._parameter_name, "mdi:heartbeat")

    async def async_update(self) -> None:
        """Update sensor state."""
        try:
            history = await self._database.get_health_parameters(self._user_id, self._parameter_name, limit=1)
            if history:
                latest = history[0]
                self._attr_native_value = latest["value"]
                self._attr_native_unit = latest["unit"]
                self._attr_extra_state_attributes = {
                    "recorded_at": latest["recorded_at"],
                    "user_id": self._user_id,
                    "history": await self._database.get_health_parameters(self._user_id, self._parameter_name, limit=10)
                }
            else:
                self._attr_native_value = None
                self._attr_native_unit = None
        except Exception as e:
            _LOGGER.error("Error updating sensor %s: %s", self._parameter_name, e)

    async def add_reading(self, value: float, unit: str) -> None:
        """Add a new reading."""
        await self._database.add_health_parameter(self._user_id, self._parameter_name, value, unit)
        await self.async_update()
