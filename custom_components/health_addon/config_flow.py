"""Config flow for Health Addon."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .utils.database import Database


class HealthAddonConfigFlow(config_entries.ConfigFlow, domain="health_addon"):
    """Handle a config flow for Health Addon."""

    VERSION = 3

    async def async_step_user(self, user_input=None):
        """Handle the initial step - select from HA persons."""
        hass = self.hass
        
        # Get persons from Home Assistant
        persons = []
        
        # Try to get from person entities
        try:
            person_entities = hass.states.async_entity_ids("person")
            for entity_id in person_entities:
                state = hass.states.get(entity_id)
                if state:
                    person_name = state.name if hasattr(state, 'name') and state.name else entity_id.split(".")[1]
                    persons.append({
                        "entity_id": entity_id,
                        "name": person_name
                    })
        except Exception:
            pass
        
        # Also get HA auth users
        try:
            users = await hass.auth.async_get_users()
            for user in users:
                if not user.system_generated:
                    persons.append({
                        "entity_id": f"user_{user.id}",
                        "name": user.name
                    })
        except Exception:
            pass
        
        # Build dropdown options
        options = {}
        
        if persons:
            # Show existing persons as selectable options
            for p in persons:
                options[p["entity_id"]] = f"👤 {p['name']}"
        
        # Always offer to skip (no person selected)
        if not persons:
            options["_none_"] = "— No person selected (manual mode) —"
        
        if user_input is not None:
            selected = user_input.get("select_person", "_none_")
            person_name = "Manual"
            
            if selected != "_none_":
                # Extract name from selected
                for p in persons:
                    if p["entity_id"] == selected:
                        person_name = p["name"]
                        break
            
            # Use selected entity_id as user_id
            user_id = selected if selected != "_none_" else f"manual_{selected}"
            
            return self.async_create_entry(
                title=f"Health Addon - {person_name}",
                data={"user_id": user_id, "name": person_name}
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("select_person", description={"suggested_value": list(options.keys())[0] if options else "_none_"}): vol.In(options)
            }),
            description_placeholders={"desc": "Select a person from Home Assistant"},
        )


class HealthAddonOptionsFlow(config_entries.OptionsFlow):
    """Options flow for Health Addon - allows reload without restart."""

    async def async_step_init(self, user_input=None):
        """Initialize options flow."""
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
            description_placeholders={"reload_note": "Reload to refresh the integration without restarting Home Assistant."},
        )


class HealthAddonOptionsFlow(config_entries.OptionsFlow):
    """Options flow for Health Addon - allows reload without restart."""

    async def async_step_init(self, user_input=None):
        """Initialize options flow."""
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
            description_placeholders={"reload_note": "Reload to refresh the integration without restarting Home Assistant."},
        )
