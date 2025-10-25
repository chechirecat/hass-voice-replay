"""Voice Replay integration - entry points (thin)."""

from __future__ import annotations

import logging

from .const import CONF_UI_URL, DATA_KEY, DEFAULT_UI_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config: dict) -> bool:
    """Set up the integration from YAML (or on startup)."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(DATA_KEY, {})

    # Lazy import to avoid importing Home Assistant modules at package import time
    from . import services as services_mod

    # Register services for immediate availability (YAML installs).
    services_mod.register_services(hass)

    return True


async def async_setup_entry(hass, entry) -> bool:
    """Set up the integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(DATA_KEY, {})

    # Lazy imports that require Home Assistant runtime
    from . import services as services_mod
    from . import ui as ui_mod

    # Ensure service registration
    services_mod.register_services(hass)

    # Read UI URL from config entry (fall back to default)
    ui_url = entry.data.get(CONF_UI_URL, DEFAULT_UI_URL)
    hass.data[DOMAIN][DATA_KEY]["ui_url"] = ui_url

    # Register the redirect view to the configured UI URL.
    ui_mod.register_ui_view(hass, ui_url)

    _LOGGER.debug("Voice Replay set up (ui_url=%s)", ui_url)
    return True


async def async_unload_entry(hass, entry) -> bool:
    """Unload a config entry."""
    # Try to remove the service (silent if not present).
    try:
        hass.services.async_remove(DOMAIN, "replay")
    except Exception:
        _LOGGER.debug("Service removal failed or service not present", exc_info=True)

    # Clear stored data for this integration instance
    hass.data.pop(DOMAIN, None)
    return True
