"""Health Addon for Home Assistant."""
import asyncio
import logging
from pathlib import Path
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from . import config_flow
from .utils.database import Database
from .utils import load_translations, set_language
from .services import async_register_services

_LOGGER = logging.getLogger(__name__)

DOMAIN = "health_addon"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Health Addon component."""
    hass.data[DOMAIN] = {"database": None}
    
    # Register reload service
    async def reload_service(call):
        """Reload Health Addon integration."""
        for entry in hass.config_entries.async_entries(DOMAIN):
            await hass.config_entries.async_reload(entry.entry_id)
    
    hass.services.async_register(DOMAIN, "reload", reload_service)
    
    # Load translations based on HA language (async)
    translations_path = Path(__file__).parent / "translations"
    ha_language = hass.config.language or "en"
    await load_translations(translations_path, ha_language)
    _LOGGER.info("Health Addon loaded with language: %s", ha_language)
    
    return True


async def async_setup_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Set up Health Addon from a config entry."""
    user_id = entry.data.get("user_id")
    user_name = entry.data.get("name", user_id)
    
    # Initialize database (global)
    if hass.data[DOMAIN]["database"] is None:
        db = Database(hass.config.path("custom_components/health_addon/health_data.db"))
        await db.init()
        hass.data[DOMAIN]["database"] = db
    
    # Add user if not exists
    db = hass.data[DOMAIN]["database"]
    await db.add_user(user_id, user_name)
    
    # Register services with user context
    await async_register_services(hass, db, user_id)

    # Create config entry data for sensors
    entry.async_on_unload(
        entry.add_update_listener(async_update_entry)
    )

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, "sensor")
    )
    return True


async def async_update_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> None:
    """Handle config entry update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Unload a config entry."""
    await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    return True
