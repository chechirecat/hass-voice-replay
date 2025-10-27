"""Voice Replay integration - entry points (thin)."""

from __future__ import annotations

import logging

from .const import DATA_KEY, DOMAIN

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
    from . import panel as panel_mod
    from . import services as services_mod
    from . import ui as ui_mod

    # Ensure service registration
    services_mod.register_services(hass)

    # Register the native UI views (no external URL needed)
    ui_mod.register_ui_view(hass)

    # Register the sidebar panel
    panel_mod.register_panel(hass)

    _LOGGER.debug("Voice Replay set up with native UI")
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
