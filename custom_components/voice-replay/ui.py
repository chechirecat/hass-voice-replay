"""Simple UI view for Voice Replay that redirects to the configured UI URL."""
from __future__ import annotations

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN

VIEW_URL = f"/api/{DOMAIN}/ui"
VIEW_NAME = f"api:{DOMAIN}:ui"


class VoiceReplayUIView(HomeAssistantView):
    """Redirect view to the configured UI URL."""

    url = VIEW_URL
    name = VIEW_NAME

    def __init__(self, target_url: str) -> None:
        super().__init__()
        self._target_url = target_url

    async def get(self, request: web.Request) -> web.Response:
        """Redirect GET to the configured UI URL."""
        raise web.HTTPFound(location=self._target_url)


def register_ui_view(hass: HomeAssistant, target_url: str) -> None:
    """Register the redirect view. Re-registering is safe (duplicates are avoided by name)."""
    # If the view is already registered, Home Assistant will ignore duplicates by name.
    hass.http.register_view(VoiceReplayUIView(target_url))
