"""Voice Replay integration - entry points (thin)."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from .const import DATA_KEY, DOMAIN

_LOGGER = logging.getLogger(__name__)


def _ensure_media_folder(hass) -> str:
    """Ensure the voice recordings media folder exists and return its path."""
    media_path = hass.config.path("media", "local", "voice-recordings")
    Path(media_path).mkdir(parents=True, exist_ok=True)
    _LOGGER.info("Voice recordings media folder ensured at: %s", media_path)
    return media_path


def _cleanup_media_folder(hass) -> None:
    """Clean up the voice recordings media folder on integration unload."""
    try:
        media_path = hass.config.path("media", "local", "voice-recordings")
        if os.path.exists(media_path):
            # Remove all files in the folder
            for filename in os.listdir(media_path):
                file_path = os.path.join(media_path, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    _LOGGER.debug("Removed voice recording file: %s", filename)

            # Remove the folder if it's empty
            try:
                os.rmdir(media_path)
                _LOGGER.info("Removed voice recordings media folder")
            except OSError:
                # Folder not empty (other files exist), leave it
                _LOGGER.debug("Voice recordings folder not removed (not empty)")
    except Exception as e:
        _LOGGER.warning("Could not cleanup voice recordings folder: %s", e)


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

    # Create the media folder for voice recordings
    media_folder_path = _ensure_media_folder(hass)
    hass.data[DOMAIN]["media_folder_path"] = media_folder_path

    # Store TTS configuration from options
    tts_config = {
        "engine": entry.options.get("tts_engine", "auto"),
        "language": entry.options.get("tts_language", "de_DE"),
        "voice": entry.options.get("tts_voice"),
        "speaker": entry.options.get("tts_speaker"),  # Add speaker support
        "sonos_announcement_mode": entry.options.get(
            "sonos_announcement_mode", "silence"
        ),
        "volume_boost_enabled": entry.options.get("volume_boost_enabled", True),
        "volume_boost_amount": entry.options.get("volume_boost_amount", 0.1),
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
        "volume_boost_enabled": entry.options.get("volume_boost_enabled", True),
        "volume_boost_amount": entry.options.get("volume_boost_amount", 0.1),
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

    # Clean up the media folder
    _cleanup_media_folder(hass)

    # Clear stored data for this integration instance
    hass.data.pop(DOMAIN, None)
    return True
