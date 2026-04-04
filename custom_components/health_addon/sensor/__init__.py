"""Sensor platform for Health Addon."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .health_parameter import HealthParameterSensor, PARAMS
from .medication import MedicationSensor
from ..utils.database import Database

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors for Health Addon."""
    db: Database = hass.data["health_addon"]["database"]
    
    entities = []
    
    # Create health parameter sensors
    for param in PARAMS:
        entities.append(HealthParameterSensor(db, param))
    
    # Create medication sensors
    medications = await db.get_medications()
    for med in medications:
        entities.append(MedicationSensor(db, med["id"], med["name"], med["dosage"]))
    
    async_add_entities(entities)
