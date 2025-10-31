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
        """Handle POST request for audio upload."""
        try:
            reader = await request.multipart()
            fields = {}

            async for field in reader:
                if field.name == "audio":
                    fields["audio"] = await field.read()
                else:
                    fields[field.name] = await field.text()

            entity_id = fields.get("entity_id")
            request_type = fields.get("type", "audio")

            if not entity_id:
                return web.json_response({"error": "Missing entity_id"}, status=400)

            # Handle TTS requests
            if request_type == "tts":
                text = fields.get("text")
                if not text:
                    return web.json_response({"error": "Missing text for TTS"}, status=400)
                return await self._handle_tts_request(entity_id, text)

            # Handle audio recording
            return await self._handle_audio_recording(entity_id, fields)

        except Exception as e:
            _LOGGER.error("Error handling upload request: %s", e)
            return web.json_response({"error": str(e)}, status=500)

    async def _handle_tts_request(self, entity_id: str, text: str) -> web.Response:
        """Handle text-to-speech request."""
        try:
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

    async def _handle_audio_recording(self, entity_id: str, fields: dict) -> web.Response:
        """Handle audio recording upload and playback."""
        import os
        import tempfile

        audio_data = fields.get("audio")
        if not audio_data:
            return web.json_response({"error": "Missing audio data"}, status=400)

        # Get content type from frontend
        provided_content_type = fields.get("content_type", "audio/webm")

        # Determine file format
        file_extension, media_content_type = self._determine_file_format(provided_content_type)

        _LOGGER.info("Processing audio upload: %s -> %s", provided_content_type, file_extension)

        # Save audio temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file.write(audio_data)
            temp_path = tmp_file.name

        # Convert WebM to MP3 if needed
        final_content_type = await self._convert_webm_to_mp3(temp_path, provided_content_type, file_extension)

        # Create a URL for serving
        media_url = f"/api/{DOMAIN}/media/{os.path.basename(temp_path)}"
        self.hass.data.setdefault(DOMAIN, {})
        self.hass.data[DOMAIN][os.path.basename(temp_path)] = temp_path

        # Schedule cleanup
        await self._schedule_file_cleanup(temp_path)

        # Play the audio
        await self._play_audio(entity_id, media_url, final_content_type, temp_path)

        return web.json_response({"status": "success", "message": "Playing audio"})

    def _determine_file_format(self, provided_content_type: str) -> tuple[str, str]:
        """Determine file extension and media content type."""
        if "mp4" in provided_content_type:
            return ".m4a", "audio/mp4"
        elif "mpeg" in provided_content_type or "mp3" in provided_content_type:
            return ".mp3", "audio/mpeg"
        elif "wav" in provided_content_type:
            return ".wav", "audio/wav"
        elif "webm" in provided_content_type:
            _LOGGER.info("WebM audio received - converting to MP3 for Sonos compatibility")
            return ".mp3", "audio/mpeg"
        else:
            return ".webm", "audio/webm"

    async def _convert_webm_to_mp3(self, temp_path: str, provided_content_type: str, file_extension: str) -> str:
        """Convert WebM to MP3 if needed and return final content type."""
        if "webm" in provided_content_type and file_extension == ".mp3":
            import os
            import shutil
            import subprocess

            if shutil.which("ffmpeg"):
                try:
                    mp3_temp_path = temp_path.replace(".mp3", "_converted.mp3")
                    subprocess.run(
                        [
                            "ffmpeg", "-i", temp_path, "-y",
                            "-acodec", "libmp3lame", "-b:a", "128k",
                            mp3_temp_path,
                        ],
                        check=True,
                        capture_output=True,
                    )
                    os.remove(temp_path)
                    os.rename(mp3_temp_path, temp_path)
                    _LOGGER.info("Successfully converted WebM to MP3")
                    return "audio/mpeg"
                except (subprocess.CalledProcessError, Exception) as e:
                    _LOGGER.error("FFmpeg conversion failed: %s", e)
                    return "audio/webm"
            else:
                _LOGGER.warning("FFmpeg not found - cannot convert WebM to MP3")
                return "audio/webm"

        return provided_content_type

    async def _schedule_file_cleanup(self, temp_path: str) -> None:
        """Schedule cleanup of temporary files after 10 minutes."""
        import asyncio
        import os

        async def cleanup_temp_file():
            await asyncio.sleep(600)  # 10 minutes
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                filename = os.path.basename(temp_path)
                if filename in self.hass.data.get(DOMAIN, {}):
                    del self.hass.data[DOMAIN][filename]
                _LOGGER.debug("Cleaned up temporary file: %s", filename)
            except Exception as cleanup_error:
                _LOGGER.warning("Could not cleanup temporary file: %s", cleanup_error)

        self.hass.async_create_task(cleanup_temp_file())

    async def _play_audio(self, entity_id: str, media_url: str, final_content_type: str, temp_path: str) -> None:
        """Play audio on the specified media player."""
        external_url = self.hass.config.external_url or "http://localhost:8123"
        full_media_url = f"{external_url}{media_url}"

        _LOGGER.info("Playing audio on %s with content type %s", entity_id, final_content_type)

        # Check if this is a Sonos speaker
        is_sonos = any(keyword in entity_id.lower() for keyword in ["sonos", "play:1", "play:3", "play:5"])

        if is_sonos:
            await self._handle_sonos_playback(entity_id, full_media_url, temp_path)
        else:
            # For non-Sonos players, use standard approach
            await self.hass.services.async_call(
                "media_player",
                "play_media",
                {
                    "entity_id": entity_id,
                    "media_content_id": full_media_url,
                    "media_content_type": final_content_type,
                },
                blocking=True,
            )

    async def _handle_sonos_playback(self, entity_id: str, full_media_url: str, temp_path: str) -> None:
        """Handle Sonos-specific playback with snapshot/restore."""
        # Create snapshot
        await self._create_sonos_snapshot(entity_id)

        # Play the audio
        success = await self._play_on_sonos(entity_id, full_media_url)
        if not success:
            raise Exception("All Sonos content types failed")

        # Schedule restoration
        await self._schedule_sonos_restore(entity_id, temp_path)

    async def _create_sonos_snapshot(self, entity_id: str) -> None:
        """Create Sonos snapshot with fallback to stop."""
        import asyncio

        try:
            _LOGGER.info("Creating Sonos snapshot before playing voice message")
            await self.hass.services.async_call(
                "sonos", "snapshot", {"entity_id": entity_id}, blocking=True,
            )
            await asyncio.sleep(0.2)
        except Exception as snapshot_error:
            _LOGGER.warning("Could not create Sonos snapshot: %s", snapshot_error)
            try:
                _LOGGER.debug("Falling back to simple stop for Sonos")
                await self.hass.services.async_call(
                    "media_player", "media_stop", {"entity_id": entity_id}, blocking=True,
                )
                await asyncio.sleep(0.5)
            except Exception as stop_error:
                _LOGGER.debug("Could not stop Sonos player: %s", stop_error)

    async def _play_on_sonos(self, entity_id: str, full_media_url: str) -> bool:
        """Try to play on Sonos with different content types."""
        sonos_content_types = ["audio/mpeg", "audio/mp3", "audio/x-mpeg"]

        for sonos_type in sonos_content_types:
            try:
                _LOGGER.info("Trying Sonos URL streaming with content type: %s", sonos_type)
                await self.hass.services.async_call(
                    "media_player",
                    "play_media",
                    {
                        "entity_id": entity_id,
                        "media_content_id": full_media_url,
                        "media_content_type": sonos_type,
                    },
                    blocking=True,
                )
                _LOGGER.info("Successfully started Sonos playback with: %s", sonos_type)
                return True
            except Exception as sonos_error:
                _LOGGER.warning("Sonos content type %s failed: %s", sonos_type, sonos_error)
                continue

        return False

    async def _schedule_sonos_restore(self, entity_id: str, temp_path: str) -> None:
        """Schedule Sonos state restoration based on audio duration."""
        import asyncio
        import os
        import subprocess

        try:
            temp_file_path = self.hass.data[DOMAIN][os.path.basename(temp_path)]
            if os.path.exists(temp_file_path):
                try:
                    result = subprocess.run([
                        "ffprobe", "-v", "quiet", "-show_entries",
                        "format=duration", "-of", "csv=p=0", temp_file_path
                    ], capture_output=True, text=True, check=True)

                    duration = float(result.stdout.strip())
                    restore_delay = max(duration + 1.0, 3.0)
                    _LOGGER.info("Scheduling Sonos restore in %.1f seconds", restore_delay)

                    async def restore_sonos():
                        await asyncio.sleep(restore_delay)
                        try:
                            await self.hass.services.async_call(
                                "sonos", "restore", {"entity_id": entity_id}, blocking=True,
                            )
                            _LOGGER.info("Sonos state restored successfully")
                        except Exception as restore_error:
                            _LOGGER.warning("Could not restore Sonos state: %s", restore_error)

                    self.hass.async_create_task(restore_sonos())
                except subprocess.CalledProcessError:
                    _LOGGER.warning("Could not determine audio duration, using fixed restore delay")
                    await self._schedule_fallback_restore(entity_id)
        except Exception as schedule_error:
            _LOGGER.warning("Could not schedule Sonos restore: %s", schedule_error)

    async def _schedule_fallback_restore(self, entity_id: str) -> None:
        """Schedule Sonos restore with fixed delay as fallback."""
        import asyncio

        async def restore_sonos_fallback():
            await asyncio.sleep(5.0)
            try:
                await self.hass.services.async_call(
                    "sonos", "restore", {"entity_id": entity_id}, blocking=True,
                )
                _LOGGER.info("Sonos state restored (fallback timing)")
            except Exception as restore_error:
                _LOGGER.warning("Could not restore Sonos state: %s", restore_error)

        self.hass.async_create_task(restore_sonos_fallback())


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
    """Serve temporary audio files without authentication for media players."""

    url = f"{MEDIA_URL}/{{filename}}"
    name = MEDIA_NAME
    requires_auth = False  # Allow unauthenticated access for media players

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
