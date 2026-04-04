"""Config flow for Health Addon."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant


class HealthAddonConfigFlow(config_entries.ConfigFlow, domain="health_addon"):
    """Handle a config flow for Health Addon."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title="Health Addon", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            description_placeholders={},
        )
