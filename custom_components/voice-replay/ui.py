"""Native UI implementation for Voice Replay with direct Home Assistant integration."""

from __future__ import annotations

import logging

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# API endpoints
UPLOAD_URL = f"/api/{DOMAIN}/upload"
UPLOAD_NAME = f"api:{DOMAIN}:upload"
MEDIA_PLAYERS_URL = f"/api/{DOMAIN}/media_players"
MEDIA_PLAYERS_NAME = f"api:{DOMAIN}:media_players"
MEDIA_URL = f"/api/{DOMAIN}/media"
MEDIA_NAME = f"api:{DOMAIN}:media"
TTS_CONFIG_URL = f"/api/{DOMAIN}/tts_config"
TTS_CONFIG_NAME = f"api:{DOMAIN}:tts_config"


class VoiceReplayUploadView(HomeAssistantView):
    """Handle audio upload and playback."""

    url = UPLOAD_URL
    name = UPLOAD_NAME
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__()
        self.hass = hass

    async def post(self, request: web.Request) -> web.Response:
        """Handle audio upload or text-to-speech and trigger playback."""
        try:
            reader = await request.multipart()

            # Read all form fields
            fields = {}
            while True:
                field = await reader.next()
                if field is None:
                    break

                field_name = field.name
                if field_name in ["audio"]:
                    fields[field_name] = await field.read()
                else:
                    fields[field_name] = (await field.read()).decode()

            entity_id = fields.get("entity_id")
            request_type = fields.get("type", "recording")

            if not entity_id:
                return web.json_response({"error": "Missing entity_id"}, status=400)

            import os
            import tempfile

            if request_type == "tts":
                # Handle text-to-speech
                text = fields.get("text")
                if not text:
                    return web.json_response(
                        {"error": "Missing text for TTS"}, status=400
                    )

                # Use Home Assistant's TTS service
                try:
                    # Call TTS service to speak directly to media player
                    await self.hass.services.async_call(
                        "tts",
                        "speak",
                        {
                            "entity_id": entity_id,
                            "message": text,
                        },
                        blocking=True,
                    )

                    return web.json_response(
                        {"status": "success", "message": "Playing TTS audio"}
                    )

                except Exception as tts_error:
                    _LOGGER.error("TTS service error: %s", tts_error)
                    return web.json_response(
                        {"error": f"TTS service failed: {str(tts_error)}"}, status=500
                    )

            else:
                # Handle audio recording
                audio_data = fields.get("audio")
                if not audio_data:
                    return web.json_response(
                        {"error": "Missing audio data"}, status=400
                    )

                # Save audio temporarily and create a media URL
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".webm"
                ) as tmp_file:
                    tmp_file.write(audio_data)
                    temp_path = tmp_file.name

                # Create a URL that Home Assistant can serve
                media_url = f"/api/{DOMAIN}/media/{os.path.basename(temp_path)}"

                # Store the file path for serving
                self.hass.data.setdefault(DOMAIN, {})
                self.hass.data[DOMAIN][os.path.basename(temp_path)] = temp_path

                # Call the media player service
                await self.hass.services.async_call(
                    "media_player",
                    "play_media",
                    {
                        "entity_id": entity_id,
                        "media_content_id": f"http://localhost:8123{media_url}",
                        "media_content_type": "audio/webm",
                    },
                    blocking=True,
                )

                return web.json_response(
                    {"status": "success", "message": "Playing audio"}
                )

        except Exception as e:
            _LOGGER.error("Error handling upload request: %s", e)
            return web.json_response({"error": str(e)}, status=500)


class VoiceReplayMediaPlayersView(HomeAssistantView):
    """Get available media players."""

    url = MEDIA_PLAYERS_URL
    name = MEDIA_PLAYERS_NAME
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__()
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        """Return list of available media players."""
        media_players = []

        for entity_id, state in self.hass.states.async_all():
            if entity_id.startswith("media_player."):
                media_players.append(
                    {
                        "entity_id": entity_id,
                        "name": state.attributes.get("friendly_name", entity_id),
                        "state": state.state,
                    }
                )

        return web.json_response(media_players)


class VoiceReplayMediaView(HomeAssistantView):
    """Serve temporary audio files."""

    url = f"{MEDIA_URL}/{{filename}}"
    name = MEDIA_NAME
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__()
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        """Serve audio file."""
        filename = request.match_info.get("filename")
        if not filename:
            return web.Response(status=404)

        # Get file path from stored data
        file_path = self.hass.data.get(DOMAIN, {}).get(filename)
        if not file_path:
            return web.Response(status=404)

        try:
            import os

            if not os.path.exists(file_path):
                return web.Response(status=404)

            with open(file_path, "rb") as f:
                content = f.read()

            return web.Response(
                body=content,
                content_type="audio/webm",
                headers={"Content-Disposition": f'inline; filename="{filename}"'},
            )
        except Exception as e:
            _LOGGER.error("Error serving media file %s: %s", filename, e)
            return web.Response(status=500)


class VoiceReplayTTSConfigView(HomeAssistantView):
    """Get TTS configuration and available services."""

    url = TTS_CONFIG_URL
    name = TTS_CONFIG_NAME
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__()
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        """Return TTS configuration."""
        try:
            # Check if TTS is available
            tts_services = []
            if self.hass.services.has_service("tts", "speak"):
                # Get available TTS engines
                tts_domain = self.hass.data.get("tts", {})
                if tts_domain:
                    for service_name in self.hass.services.async_services().get(
                        "tts", {}
                    ):
                        tts_services.append(service_name)
                else:
                    # Fallback - assume basic TTS is available
                    tts_services.append("speak")

            return web.json_response(
                {
                    "available": len(tts_services) > 0,
                    "services": tts_services,
                    "default_service": "speak" if tts_services else None,
                }
            )
        except Exception as e:
            _LOGGER.error("Error getting TTS config: %s", e)
            return web.json_response({"available": False, "error": str(e)})


def register_ui_view(hass: HomeAssistant, target_url: str = None) -> None:
    """Register the API views for backend functionality."""
    hass.http.register_view(VoiceReplayUploadView(hass))
    hass.http.register_view(VoiceReplayMediaPlayersView(hass))
    hass.http.register_view(VoiceReplayMediaView(hass))
    hass.http.register_view(VoiceReplayTTSConfigView(hass))

    _LOGGER.debug("API views registered - frontend card is in separate repository")
