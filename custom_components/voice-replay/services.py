"""Service registration for voice-replay."""
from __future__ import annotations

import logging
from .const import DOMAIN, SERVICE_REPLAY, DATA_KEY
from homeassistant.core import HomeAssistant, ServiceCall
from typing import Any

_LOGGER = logging.getLogger(__name__)


def register_services(hass: HomeAssistant) -> None:
    """Register services if not already registered."""
    if hass.services.has_service(DOMAIN, SERVICE_REPLAY):
        return

    async def handle_replay(call: ServiceCall) -> None:
        """Handle the replay service call."""
        payload: dict[str, Any] = {
            "url": call.data.get("url"),
            "media_content": call.data.get("media_content"),
            "entity_id": call.data.get("entity_id"),
        }
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN].setdefault(DATA_KEY, {})
        hass.data[DOMAIN][DATA_KEY]["last_replay"] = payload
        _LOGGER.info("voice-replay.replay called: %s", payload)

    hass.services.async_register(DOMAIN, SERVICE_REPLAY, handle_replay)
