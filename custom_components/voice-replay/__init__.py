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

    # Store TTS configuration from options
    tts_config = {
        "engine": entry.options.get("tts_engine", "auto"),
        "language": entry.options.get("tts_language", "de_DE"),
        "voice": entry.options.get("tts_voice"),
        "speaker": entry.options.get("tts_speaker"),  # Add speaker support
        "sonos_announcement_mode": entry.options.get(
            "sonos_announcement_mode", "silence"
        ),
    }
    hass.data[DOMAIN]["tts_config"] = tts_config

    # Lazy imports that require Home Assistant runtime
    from . import services as services_mod
    from . import ui as ui_mod

    # Ensure service registration
    services_mod.register_services(hass)

    # Register the API views for backend functionality
    ui_mod.register_ui_view(hass)

    # Listen for options updates
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    _LOGGER.debug(
        "Voice Replay integration set up successfully with TTS config: %s", tts_config
    )
    return True


async def async_update_options(hass, entry) -> None:
    """Update options when they change."""
    # Update stored TTS configuration
    tts_config = {
        "engine": entry.options.get("tts_engine", "auto"),
        "language": entry.options.get("tts_language", "de_DE"),
        "voice": entry.options.get("tts_voice"),
        "speaker": entry.options.get("tts_speaker"),  # Add speaker support
        "sonos_announcement_mode": entry.options.get(
            "sonos_announcement_mode", "silence"
        ),
    }
    hass.data[DOMAIN]["tts_config"] = tts_config
    _LOGGER.debug("Updated TTS config: %s", tts_config)


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
