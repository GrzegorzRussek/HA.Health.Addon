"""Config flow for Health Addon."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .utils.database import Database


class HealthAddonConfigFlow(config_entries.ConfigFlow, domain="health_addon"):
    """Handle a config flow for Health Addon."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step - select or create user."""
        hass = self.hass
        
        # Get existing users from database
        db: Database = hass.data.get("health_addon", {}).get("database")
        
        if db:
            users = await db.get_users()
        else:
            users = []
        
        # Build schema
        schema = {}
        
        if users:
            # Option to select existing user
            user_options = {u["user_id"]: u["name"] for u in users}
            schema["select_user"] = vol.In selection({
                "new": "➕ Add New User",
                **{uid: name for uid, name in user_options.items()}
            })
        
        # Always offer option to add new user
        if not users:
            schema["name"] = str
            schema["user_id"] = str
        
        if user_input is not None:
            if user_input.get("select_user") == "new" or not users:
                # Show form to create new user
                return await self.async_step_new_user(user_input)
            else:
                # Use existing user
                user_id = user_input.get("select_user")
                return self.async_create_entry(
                    title=f"Health Addon - {users[[u['user_id'] for u in users].index(user_id)]['name']}",
                    data={"user_id": user_id}
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema),
            description_placeholders={},
        )

    async def async_step_new_user(self, user_input=None):
        """Handle creating a new user."""
        schema = {
            vol.Required("user_id"): str,
            vol.Required("name"): str,
        }

        if user_input is not None:
            user_id = user_input["user_id"]
            name = user_input["name"]
            
            # Store in database
            db: Database = self.hass.data.get("health_addon", {}).get("database")
            if db:
                await db.add_user(user_id, name)
            
            return self.async_create_entry(
                title=f"Health Addon - {name}",
                data={"user_id": user_id, "name": name}
            )

        return self.async_show_form(
            step_id="new_user",
            data_schema=vol.Schema(schema),
            description_placeholders={},
        )
