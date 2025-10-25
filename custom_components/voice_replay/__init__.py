"""Voice Replay integration - entry points (thin)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, DATA_KEY, CONF_UI_URL, DEFAULT_UI_URL

_LOGGER = logging.getLogger(__name__)

# Minimal imports for helpers
from . import services as services_mod
from . import ui as ui_mod


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
	"""Set up the integration from YAML (or on startup)."""
	hass.data.setdefault(DOMAIN, {})
	hass.data[DOMAIN].setdefault(DATA_KEY, {})

	# Register services for immediate availability (YAML installs).
	services_mod.register_services(hass)

	return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
	"""Set up the integration from a config entry."""
	hass.data.setdefault(DOMAIN, {})
	hass.data[DOMAIN].setdefault(DATA_KEY, {})

	# Ensure service registration
	services_mod.register_services(hass)

	# Read UI URL from config entry (fall back to default)
	ui_url = entry.data.get(CONF_UI_URL, DEFAULT_UI_URL)
	hass.data[DOMAIN][DATA_KEY]["ui_url"] = ui_url

	# Register a small HTTP view that redirects to the configured UI URL.
	ui_mod.register_ui_view(hass, ui_url)

	_LOGGER.debug("Voice Replay set up (ui_url=%s)", ui_url)
	return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
	"""Unload a config entry."""
	# Try to remove the service (silent if not present).
	try:
		hass.services.async_remove(DOMAIN, "replay")
	except Exception:
		_LOGGER.debug("Service removal failed or service not present", exc_info=True)

	# Clear stored data for this integration instance
	hass.data.pop(DOMAIN, None)
	return True