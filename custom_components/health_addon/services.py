"""Services for Health Addon."""
import logging
from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall

from .utils.database import Database

_LOGGER = logging.getLogger(__name__)

DOMAIN = "health_addon"

SERVICE_ADD_PARAMETER = "add_health_parameter"
SERVICE_ADD_MEDICATION = "add_medication"
SERVICE_LOG_DOSE = "log_dose"
SERVICE_UPDATE_QUANTITY = "update_quantity"
SERVICE_DELETE_MEDICATION = "delete_medication"
SERVICE_GET_MEDICATIONS = "get_medications"
SERVICE_GET_HISTORY = "get_history"
SERVICE_GET_ALL_MEDICATIONS = "get_all_medications"


async def async_register_services(hass: HomeAssistant, database: Database, user_id: str) -> None:
    """Register services for Health Addon."""

    async def add_health_parameter(call: ServiceCall) -> dict:
        """Add a health parameter reading."""
        # Get user_id from service data or use the one from config entry
        param_user_id = call.data.get("user_id", user_id)
        name = call.data.get("name")
        value = call.data.get("value")
        unit = call.data.get("unit", "")
        
        if not name or value is None:
            _LOGGER.error("Missing name or value for health parameter")
            return {"success": False, "error": "Missing name or value"}
        
        await database.add_health_parameter(param_user_id, name, float(value), unit)
        _LOGGER.info("Added health parameter for %s: %s = %s %s", param_user_id, name, value, unit)
        return {"success": True}

    async def add_medication(call: ServiceCall) -> dict:
        """Add a medication to inventory."""
        param_user_id = call.data.get("user_id", user_id)
        name = call.data.get("name")
        dosage = call.data.get("dosage")
        barcode = call.data.get("barcode")
        expiration_date = call.data.get("expiration_date")
        quantity = call.data.get("quantity", 0)
        schedule = call.data.get("schedule")
        
        if not name or not dosage:
            _LOGGER.error("Missing name or dosage for medication")
            return {"success": False, "error": "Missing name or dosage"}
        
        med_id = await database.add_medication(param_user_id, name, dosage, barcode, expiration_date, quantity, schedule)
        _LOGGER.info("Added medication for %s: %s (%s), schedule: %s", param_user_id, name, dosage, schedule)
        return {"success": True, "medication_id": med_id}

    async def log_dose(call: ServiceCall) -> dict:
        """Log that a dose was taken."""
        param_user_id = call.data.get("user_id", user_id)
        medication_id = call.data.get("medication_id")
        
        if not medication_id:
            _LOGGER.error("Missing medication_id")
            return {"success": False, "error": "Missing medication_id"}
        
        await database.log_medication_taken(param_user_id, medication_id)
        _LOGGER.info("Logged dose for %s, medication_id: %s", param_user_id, medication_id)
        return {"success": True}

    async def update_quantity(call: ServiceCall) -> dict:
        """Update medication quantity."""
        param_user_id = call.data.get("user_id", user_id)
        medication_id = call.data.get("medication_id")
        quantity = call.data.get("quantity")
        
        if not medication_id or quantity is None:
            return {"success": False, "error": "Missing medication_id or quantity"}
        
        await database.update_medication(param_user_id, medication_id, quantity=quantity)
        return {"success": True}

    async def delete_medication(call: ServiceCall) -> dict:
        """Delete a medication."""
        param_user_id = call.data.get("user_id", user_id)
        medication_id = call.data.get("medication_id")
        
        if not medication_id:
            return {"success": False, "error": "Missing medication_id"}
        
        await database.delete_medication(param_user_id, medication_id)
        return {"success": True}

    async def get_medications(call: ServiceCall) -> dict:
        """Get medications for current user."""
        param_user_id = call.data.get("user_id", user_id)
        meds = await database.get_medications(param_user_id)
        return {"medications": meds}

    async def get_all_medications(call: ServiceCall) -> dict:
        """Get all medications across all users (for admin dashboard)."""
        meds = await database.get_medications()
        return {"medications": meds}

    async def get_history(call: ServiceCall) -> dict:
        """Get health parameter history."""
        param_user_id = call.data.get("user_id", user_id)
        name = call.data.get("name")
        limit = call.data.get("limit", 100)
        
        if not name:
            return {"success": False, "error": "Missing name"}
        
        history = await database.get_health_parameters(param_user_id, name, limit)
        return {"history": history}

    # Register services with per-user user_id
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_PARAMETER,
        add_health_parameter,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_MEDICATION,
        add_medication,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_LOG_DOSE,
        log_dose,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_QUANTITY,
        update_quantity,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_MEDICATION,
        delete_medication,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_MEDICATIONS,
        get_medications,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_ALL_MEDICATIONS,
        get_all_medications,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_HISTORY,
        get_history,
    )
    
    _LOGGER.info("Health Addon services registered for user %s", user_id)
