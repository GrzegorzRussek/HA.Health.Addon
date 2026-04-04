"""Health Addon for Home Assistant."""
import asyncio
import logging
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .utils.database import Database
from .services import async_register_services

_LOGGER = logging.getLogger(__name__)

DOMAIN = "health_addon"

CONFIG_SCHEMA = config_entries.ConfigSchema({DOMAIN: {}})


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Health Addon component."""
    hass.data[DOMAIN] = {"database": None}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Set up Health Addon from a config entry."""
    database = Database(hass.config.path("custom_components/health_addon/health_data.db"))
    await database.init()
    hass.data[DOMAIN]["database"] = database

    # Register services
    await async_register_services(hass, database)

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Unload a config entry."""
    await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    db: Database = hass.data[DOMAIN].get("database")
    if db:
        await db.close()
    return True
