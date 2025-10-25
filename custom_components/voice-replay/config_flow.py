"""Config flow for Voice Replay."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries

from .const import CONF_UI_URL, DEFAULT_UI_URL, DOMAIN


class VoiceReplayFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Voice Replay."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="Voice Replay", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Optional(CONF_UI_URL, default=DEFAULT_UI_URL): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
