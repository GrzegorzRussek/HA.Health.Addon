"""Services for Health Addon."""
import logging
from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_platform

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


async def async_register_services(hass: HomeAssistant, database: Database) -> None:
    """Register services for Health Addon."""

    async def add_health_parameter(call: ServiceCall) -> dict:
        """Add a health parameter reading."""
        name = call.data.get("name")
        value = call.data.get("value")
        unit = call.data.get("unit", "")
        
        if not name or value is None:
            _LOGGER.error("Missing name or value for health parameter")
            return {"success": False, "error": "Missing name or value"}
        
        await database.add_health_parameter(name, float(value), unit)
        _LOGGER.info("Added health parameter: %s = %s %s", name, value, unit)
        return {"success": True}

    async def add_medication(call: ServiceCall) -> dict:
        """Add a medication to inventory."""
        name = call.data.get("name")
        dosage = call.data.get("dosage")
        barcode = call.data.get("barcode")
        expiration_date = call.data.get("expiration_date")
        quantity = call.data.get("quantity", 0)
        
        if not name or not dosage:
            _LOGGER.error("Missing name or dosage for medication")
            return {"success": False, "error": "Missing name or dosage"}
        
        med_id = await database.add_medication(name, dosage, barcode, expiration_date, quantity)
        _LOGGER.info("Added medication: %s (%s)", name, dosage)
        return {"success": True, "medication_id": med_id}

    async def log_dose(call: ServiceCall) -> dict:
        """Log that a dose was taken."""
        medication_id = call.data.get("medication_id")
        
        if not medication_id:
            _LOGGER.error("Missing medication_id")
            return {"success": False, "error": "Missing medication_id"}
        
        await database.log_medication_taken(medication_id)
        _LOGGER.info("Logged dose for medication_id: %s", medication_id)
        return {"success": True}

    async def update_quantity(call: ServiceCall) -> dict:
        """Update medication quantity."""
        medication_id = call.data.get("medication_id")
        quantity = call.data.get("quantity")
        
        if not medication_id or quantity is None:
            return {"success": False, "error": "Missing medication_id or quantity"}
        
        await database.update_medication(medication_id, quantity=quantity)
        return {"success": True}

    async def delete_medication(call: ServiceCall) -> dict:
        """Delete a medication."""
        medication_id = call.data.get("medication_id")
        
        if not medication_id:
            return {"success": False, "error": "Missing medication_id"}
        
        await database.delete_medication(medication_id)
        return {"success": True}

    async def get_medications(call: ServiceCall) -> dict:
        """Get all medications."""
        meds = await database.get_medications()
        return {"medications": meds}

    async def get_history(call: ServiceCall) -> dict:
        """Get health parameter history."""
        name = call.data.get("name")
        limit = call.data.get("limit", 100)
        
        if not name:
            return {"success": False, "error": "Missing name"}
        
        history = await database.get_health_parameters(name, limit)
        return {"history": history}

    # Register services
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
        SERVICE_GET_HISTORY,
        get_history,
    )
    
    _LOGGER.info("Health Addon services registered")
