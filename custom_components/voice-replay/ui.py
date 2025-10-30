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

                # Get content type from frontend if provided
                provided_content_type = fields.get("content_type", "audio/webm")

                # Determine file extension and media content type
                file_extension = ".webm"  # default
                media_content_type = provided_content_type

                if "mp4" in provided_content_type:
                    file_extension = ".m4a"
                    media_content_type = "audio/mp4"
                elif "mpeg" in provided_content_type or "mp3" in provided_content_type:
                    file_extension = ".mp3"
                    media_content_type = "audio/mpeg"
                elif "wav" in provided_content_type:
                    file_extension = ".wav"
                    media_content_type = "audio/wav"
                elif "webm" in provided_content_type:
                    # Convert WebM to MP3 for Sonos compatibility
                    _LOGGER.info(
                        "WebM audio received - converting to MP3 for Sonos compatibility"
                    )
                    file_extension = ".mp3"
                    # Use 'music' content type for Sonos compatibility
                    media_content_type = "music"
                else:
                    # Default to webm
                    file_extension = ".webm"
                    media_content_type = "audio/webm"

                _LOGGER.info(
                    "Processing audio upload: %s -> %s",
                    provided_content_type,
                    file_extension,
                )

                # Save audio temporarily with correct extension
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=file_extension
                ) as tmp_file:
                    tmp_file.write(audio_data)
                    temp_path = tmp_file.name

                # Convert WebM to MP3 if needed
                if "webm" in provided_content_type and file_extension == ".mp3":
                    import os
                    import shutil
                    import subprocess

                    # Check if ffmpeg is available
                    if shutil.which("ffmpeg"):
                        try:
                            # Create temporary MP3 file
                            mp3_temp_path = temp_path.replace(".mp3", "_converted.mp3")

                            # Convert using ffmpeg
                            subprocess.run(
                                [
                                    "ffmpeg",
                                    "-i",
                                    temp_path,
                                    "-y",
                                    "-acodec",
                                    "libmp3lame",
                                    "-b:a",
                                    "128k",
                                    mp3_temp_path,
                                ],
                                check=True,
                                capture_output=True,
                            )

                            # Replace original with converted file
                            os.remove(temp_path)
                            os.rename(mp3_temp_path, temp_path)

                            _LOGGER.info("Successfully converted WebM to MP3")

                        except subprocess.CalledProcessError as e:
                            _LOGGER.error("FFmpeg conversion failed: %s", e)
                            # Fall back to original file
                            media_content_type = "audio/webm"
                        except Exception as e:
                            _LOGGER.error("Audio conversion error: %s", e)
                            # Fall back to original file
                            media_content_type = "audio/webm"
                    else:
                        _LOGGER.warning("FFmpeg not found - cannot convert WebM to MP3")
                        # Fall back to original content type
                        media_content_type = "audio/webm"

                # Create a URL that Home Assistant can serve
                media_url = f"/api/{DOMAIN}/media/{os.path.basename(temp_path)}"

                # Store the file path for serving
                self.hass.data.setdefault(DOMAIN, {})
                self.hass.data[DOMAIN][os.path.basename(temp_path)] = temp_path

                # Play media with the final content type
                final_content_type = media_content_type
                _LOGGER.info(
                    "Playing %s on %s with content type %s",
                    file_extension,
                    entity_id,
                    final_content_type,
                )

                # Try to play the media
                try:
                    await self.hass.services.async_call(
                        "media_player",
                        "play_media",
                        {
                            "entity_id": entity_id,
                            "media_content_id": f"http://localhost:8123{media_url}",
                            "media_content_type": final_content_type,
                        },
                        blocking=True,
                    )
                except Exception as play_error:
                    # If MP3 fails on Sonos, try alternative content types
                    if (
                        "does not support media content type" in str(play_error)
                        and file_extension == ".mp3"
                    ):
                        _LOGGER.warning(
                            "Initial content type %s failed: %s",
                            final_content_type,
                            play_error,
                        )

                        # Try alternative content types for MP3
                        alternative_types = [
                            "music",
                            "audio/mpeg",
                            "audio/x-mp3",
                            "application/octet-stream",
                        ]

                        for alt_type in alternative_types:
                            if alt_type == final_content_type:
                                continue  # Skip the one we already tried

                            _LOGGER.info(
                                "Trying alternative content type: %s",
                                alt_type,
                            )
                            try:
                                await self.hass.services.async_call(
                                    "media_player",
                                    "play_media",
                                    {
                                        "entity_id": entity_id,
                                        "media_content_id": f"http://localhost:8123{media_url}",
                                        "media_content_type": alt_type,
                                    },
                                    blocking=True,
                                )
                                _LOGGER.info(
                                    "Successfully played with content type: %s",
                                    alt_type,
                                )
                                break
                            except Exception as alt_error:
                                _LOGGER.warning(
                                    "Content type %s also failed: %s",
                                    alt_type,
                                    alt_error,
                                )
                                continue
                        else:
                            # All content types failed, re-raise the original error
                            raise play_error
                    else:
                        # Not a content type error or not an MP3, re-raise
                        raise play_error

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

        _LOGGER.info("Processing media players request...")

        for state in self.hass.states.async_all():
            if state.entity_id.startswith("media_player."):
                player_info = {
                    "entity_id": state.entity_id,
                    "name": state.attributes.get("friendly_name", state.entity_id),
                    "state": state.state,
                }
                media_players.append(player_info)
                _LOGGER.debug(
                    "Added media player: %s (%s) - %s",
                    player_info["name"],
                    player_info["entity_id"],
                    player_info["state"],
                )

        _LOGGER.info("Found %d media players total", len(media_players))
        _LOGGER.debug("Returning media players: %s", [p["name"] for p in media_players])

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

            # Determine content type from file extension
            content_type = "audio/webm"  # default
            if filename.endswith(".m4a"):
                content_type = "audio/mp4"
            elif filename.endswith(".mp3"):
                content_type = "audio/mpeg"
            elif filename.endswith(".wav"):
                content_type = "audio/wav"
            elif filename.endswith(".webm"):
                content_type = "audio/webm"

            return web.Response(
                body=content,
                content_type=content_type,
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
