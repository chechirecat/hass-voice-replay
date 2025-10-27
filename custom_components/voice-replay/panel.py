"""Panel registration for Voice Replay."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from .const import DOMAIN


def register_panel(hass: HomeAssistant) -> None:
    """Register the Voice Replay panel in the sidebar."""
    hass.components.frontend.async_register_built_in_panel(
        component_name="iframe",
        sidebar_title="Voice Replay",
        sidebar_icon="mdi:microphone",
        frontend_url_path="voice-replay",
        config={"url": f"/api/{DOMAIN}/panel", "title": "Voice Replay"},
        require_admin=False,
    )
