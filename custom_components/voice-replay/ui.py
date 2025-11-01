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
                    return web.json_response(
                        {"error": "Missing text for TTS"}, status=400
                    )
                return await self._handle_tts_request(entity_id, text)

            # Handle audio recording
            return await self._handle_audio_recording(entity_id, fields)

        except Exception as e:
            _LOGGER.error("Error handling upload request: %s", e)
            return web.json_response({"error": str(e)}, status=500)

    async def _handle_tts_request(self, entity_id: str, text: str) -> web.Response:
        """Handle text-to-speech request using configured TTS settings."""
        try:
            # Get TTS configuration from integration data
            tts_config = self.hass.data.get(DOMAIN, {}).get("tts_config", {})
            _LOGGER.info("Retrieved TTS config from hass.data: %s", tts_config)

            # Get volume control settings
            volume_boost_enabled = tts_config.get("volume_boost_enabled", True)
            volume_boost_amount = tts_config.get("volume_boost_amount", 0.1)

            # Store original volume if volume boost is enabled
            original_volume = None
            if volume_boost_enabled:
                original_volume = await self._store_and_boost_volume(
                    entity_id, volume_boost_amount
                )

            # Get configured settings
            configured_engine = tts_config.get("engine", "auto")
            configured_language = tts_config.get("language", "de_DE")
            configured_voice = tts_config.get("voice")
            configured_speaker = tts_config.get("speaker")  # Add speaker support

            _LOGGER.info(
                "TTS request - Engine: %s, Language: %s, Voice: %s, Speaker: %s",
                configured_engine,
                configured_language,
                configured_voice,
                configured_speaker,
            )

            # Determine which TTS engine to use
            if configured_engine == "auto":
                tts_entity = await self._get_available_tts_engine()
                _LOGGER.info("Auto-detected TTS engine: %s", tts_entity)
            else:
                # Use configured engine if it exists and is available
                state = self.hass.states.get(configured_engine)
                if state and state.state != "unavailable":
                    tts_entity = configured_engine
                    _LOGGER.info("Using configured TTS engine: %s", tts_entity)
                else:
                    _LOGGER.warning(
                        "Configured TTS engine %s not available, falling back to auto-detect",
                        configured_engine,
                    )
                    tts_entity = await self._get_available_tts_engine()
                    _LOGGER.info("Fallback TTS engine: %s", tts_entity)

            if not tts_entity:
                return web.json_response(
                    {"error": "No TTS engine available"}, status=400
                )

            _LOGGER.info(
                "Using TTS engine: %s for entity: %s (lang=%s, voice=%s, speaker=%s)",
                tts_entity,
                entity_id,
                configured_language,
                configured_voice,
                configured_speaker,
            )

            # Prepare options dict for voice and speaker selection (Wyoming Protocol compatible)
            options: dict | None = None
            if configured_voice:
                # Validate requested voice against engine voices, if available
                available_voices = await self._get_engine_voices(tts_entity)
                if available_voices and configured_voice not in available_voices:
                    _LOGGER.warning(
                        "Configured voice '%s' not available for engine %s. Available: %s. Using engine default.",
                        configured_voice,
                        tts_entity,
                        available_voices,
                    )
                else:
                    # Start building options with the voice
                    options = {"voice": configured_voice}

                    # Add speaker if configured (Wyoming Protocol)
                    if configured_speaker:
                        # Check if this is a Wyoming TTS entity that supports speakers
                        if await self._is_wyoming_tts(tts_entity):
                            options["speaker"] = configured_speaker
                            _LOGGER.info(
                                "Adding Wyoming Protocol speaker option: %s",
                                configured_speaker,
                            )
                        else:
                            # For non-Wyoming engines, some may still support speaker in voice name
                            # Try combining voice and speaker (e.g., "voice_name-speaker_name")
                            combined_voice = f"{configured_voice}-{configured_speaker}"
                            if combined_voice in (available_voices or []):
                                options["voice"] = combined_voice
                                _LOGGER.info(
                                    "Using combined voice-speaker name: %s",
                                    combined_voice,
                                )
                            else:
                                _LOGGER.warning(
                                    "Speaker '%s' not supported by non-Wyoming engine %s, ignoring",
                                    configured_speaker,
                                    tts_entity,
                                )

            # Normalize language for the engine
            normalized_language = configured_language
            if configured_language:
                normalized_language = await self._normalize_language_for_engine(
                    tts_entity, configured_language
                )
                _LOGGER.info(
                    "Language normalized: %s -> %s for engine %s",
                    configured_language,
                    normalized_language,
                    tts_entity,
                )
            else:
                _LOGGER.warning("No language configured - TTS will use engine default")

            # For Sonos speakers, prepare the message with silence/announcement
            is_sonos = any(
                keyword in entity_id.lower()
                for keyword in ["sonos", "play:1", "play:3", "play:5"]
            )
            if is_sonos:
                _LOGGER.info(
                    "Detected Sonos speaker, preparing message with silence..."
                )
                # Create snapshot first
                try:
                    await self.hass.services.async_call(
                        "sonos", "snapshot", {"entity_id": entity_id}, blocking=True
                    )
                except Exception as sonos_prep_error:
                    _LOGGER.warning(
                        "Could not create Sonos snapshot: %s", sonos_prep_error
                    )

                # Add silence or announcement to the beginning of the text
                text = await self._prepare_sonos_message(text, tts_entity)

            # Call the TTS entity service
            payload = {
                "entity_id": tts_entity,  # The TTS engine entity
                "media_player_entity_id": entity_id,  # The media player to play on
                "message": text,
                "cache": True,
            }

            # Force German language for debugging - remove this later
            if normalized_language:
                payload["language"] = normalized_language
                _LOGGER.info("Using normalized language: %s", normalized_language)
            else:
                # Fallback to force German if no language detected
                payload["language"] = "de_DE"
                _LOGGER.warning("No language configured, forcing German (de_DE)")

            if options:
                payload["options"] = options

            _LOGGER.info("TTS payload: %s", payload)

            # Log the actual service call for debugging
            _LOGGER.info("Calling tts.speak service with payload: %s", payload)
            await self.hass.services.async_call("tts", "speak", payload, blocking=True)
            _LOGGER.info("TTS service call completed successfully")

            # Schedule volume restoration if volume boost was enabled
            if volume_boost_enabled and original_volume is not None:
                await self._schedule_volume_restore(
                    entity_id, original_volume, is_sonos
                )

            # For Sonos, schedule restoration after a delay
            if is_sonos:

                async def restore_sonos():
                    import asyncio

                    await asyncio.sleep(10.0)  # Wait for TTS to finish
                    try:
                        await self.hass.services.async_call(
                            "sonos", "restore", {"entity_id": entity_id}, blocking=True
                        )
                        _LOGGER.info("Sonos state restored after TTS")
                    except Exception as restore_error:
                        _LOGGER.warning(
                            "Could not restore Sonos state: %s", restore_error
                        )

                self.hass.async_create_task(restore_sonos())

            return web.json_response({
                "status": "success",
                "message": f"Playing TTS audio via {tts_entity}",
            })

        except Exception as tts_error:
            error_msg = str(tts_error)

            # Provide more specific error messages for common issues
            if "language" in error_msg.lower():
                _LOGGER.error(
                    "TTS language error for engine %s with language '%s': %s",
                    tts_entity,
                    configured_language,
                    tts_error,
                )
                return web.json_response(
                    {
                        "error": f"Language '{configured_language}' not supported by {tts_entity}. {error_msg}"
                    },
                    status=400,
                )
            elif "voice" in error_msg.lower():
                _LOGGER.error(
                    "TTS voice error for engine %s with voice '%s': %s",
                    tts_entity,
                    configured_voice,
                    tts_error,
                )
                return web.json_response(
                    {
                        "error": f"Voice '{configured_voice}' not supported by {tts_entity}. {error_msg}"
                    },
                    status=400,
                )
            else:
                _LOGGER.error("TTS service error: %s", tts_error)
                return web.json_response(
                    {"error": f"TTS service failed: {error_msg}"}, status=500
                )

    async def _get_available_tts_engine(self) -> str | None:
        """Find an available TTS engine entity."""
        # Check for common TTS entities
        common_tts_engines = [
            "tts.piper",
            "tts.google_translate",
            "tts.amazon_polly",
            "tts.microsoft",
            "tts.voicerss",
            "tts.picotts",
        ]

        # First try common engines
        for engine in common_tts_engines:
            if self.hass.states.get(engine) is not None:
                _LOGGER.debug("Found TTS engine: %s", engine)
                return engine

        # Fallback: look for any tts.* entity
        for state in self.hass.states.async_all():
            if state.entity_id.startswith("tts.") and state.state != "unavailable":
                _LOGGER.debug("Found fallback TTS engine: %s", state.entity_id)
                return state.entity_id

        _LOGGER.warning("No TTS engine found")
        return None

    async def _get_engine_voices(self, engine_entity_id: str) -> list[str]:
        """Return a list of available voices for a given TTS engine entity."""
        try:
            state = self.hass.states.get(engine_entity_id)
            if not state:
                return []

            voices = state.attributes.get("voices") or state.attributes.get(
                "available_voices"
            )
            if voices and isinstance(voices, (list, tuple)):
                return list(voices)
        except Exception as e:
            _LOGGER.debug("Could not get voices for %s: %s", engine_entity_id, e)
        return []

    async def _normalize_language_for_engine(
        self, engine_entity_id: str, language: str
    ) -> str:
        """Normalize language code for the specific TTS engine."""
        try:
            state = self.hass.states.get(engine_entity_id)
            if not state:
                _LOGGER.warning("TTS engine state not found: %s", engine_entity_id)
                return language

            # Get supported languages from the engine
            supported_langs = state.attributes.get(
                "supported_languages"
            ) or state.attributes.get("languages")
            if not supported_langs:
                _LOGGER.warning(
                    "No supported languages found for engine %s", engine_entity_id
                )
                return language

            _LOGGER.info(
                "Engine %s supports languages: %s, requesting: %s",
                engine_entity_id,
                supported_langs,
                language,
            )

            # If the current language is supported, use it as-is
            if language in supported_langs:
                _LOGGER.info(
                    "Language '%s' is directly supported by %s",
                    language,
                    engine_entity_id,
                )
                return language

            # Try common format variations
            language_variations = []
            if language == "de":
                language_variations = ["de_DE", "de-DE", "german"]
            elif language == "en":
                language_variations = ["en_US", "en-US", "english"]
            elif language == "fr":
                language_variations = ["fr_FR", "fr-FR", "french"]
            elif language == "es":
                language_variations = ["es_ES", "es-ES", "spanish"]
            elif language == "it":
                language_variations = ["it_IT", "it-IT", "italian"]
            elif language == "de-DE":
                language_variations = ["de_DE", "de", "german"]
            elif language == "de_DE":
                language_variations = ["de-DE", "de", "german"]
            elif language in ["en-US", "en_US"]:
                language_variations = ["en_US", "en-US", "en", "english"]
            elif language in ["en-GB", "en_GB"]:
                language_variations = ["en_GB", "en-GB", "en", "english"]

            # Check if any variation is supported
            for variation in language_variations:
                if variation in supported_langs:
                    _LOGGER.info(
                        "Language mapping: '%s' -> '%s' for engine %s",
                        language,
                        variation,
                        engine_entity_id,
                    )
                    return variation

            # If no variation found, log available languages for debugging
            _LOGGER.warning(
                "Language '%s' not found for engine %s. Supported languages: %s. Using original language.",
                language,
                engine_entity_id,
                supported_langs,
            )
            return language

        except Exception as e:
            _LOGGER.debug(
                "Could not normalize language for %s: %s", engine_entity_id, e
            )
            return language

    async def _prepare_sonos_message(self, text: str, tts_entity: str) -> str:
        """Prepare TTS message for Sonos with silence or announcement."""
        try:
            # Get the configured announcement mode
            tts_config = self.hass.data.get(DOMAIN, {}).get("tts_config", {})
            announcement_mode = tts_config.get("sonos_announcement_mode", "silence")

            _LOGGER.info("Preparing Sonos message with mode: %s", announcement_mode)

            if announcement_mode == "disabled":
                # No modification needed
                return text
            elif announcement_mode == "announcement":
                # Add a verbal announcement with natural pause
                # Use language-appropriate announcement text
                tts_language = tts_config.get("language", "de_DE").lower()
                if "de" in tts_language:
                    announcement_text = "Achtung"
                elif "en" in tts_language:
                    announcement_text = "Attention"
                elif "fr" in tts_language:
                    announcement_text = "Attention"
                elif "es" in tts_language:
                    announcement_text = "Atención"
                elif "it" in tts_language:
                    announcement_text = "Attenzione"
                else:
                    announcement_text = "Attention"  # Default to English

                _LOGGER.info(
                    "Using verbal announcement for Sonos preparation: %s",
                    announcement_text,
                )
                return f"{announcement_text}... {text}"
            else:  # announcement_mode == "silence"
                # Try to use SSML for silence
                state = self.hass.states.get(tts_entity)
                if state:
                    # Check if engine supports SSML (most modern TTS engines do)
                    supported_options = state.attributes.get("supported_options", [])
                    supports_ssml = "ssml" in supported_options or "SSML" in str(
                        state.attributes
                    )

                    if supports_ssml or "piper" in tts_entity.lower():
                        # Use SSML to add 3 seconds of silence before the text
                        _LOGGER.info("Using SSML silence for Sonos preparation")
                        return f'<speak><break time="3s"/>{text}</speak>'

                # Fallback to verbal announcement if SSML not supported
                _LOGGER.info("SSML not supported, falling back to verbal announcement")
                tts_language = tts_config.get("language", "de_DE").lower()
                if "de" in tts_language:
                    announcement_text = "Achtung"
                elif "en" in tts_language:
                    announcement_text = "Attention"
                elif "fr" in tts_language:
                    announcement_text = "Attention"
                elif "es" in tts_language:
                    announcement_text = "Atención"
                elif "it" in tts_language:
                    announcement_text = "Attenzione"
                else:
                    announcement_text = "Attention"  # Default to English
                return f"{announcement_text}... {text}"

        except Exception as e:
            _LOGGER.warning("Could not prepare Sonos message, using original: %s", e)
            return text

    async def _store_and_boost_volume(
        self, entity_id: str, volume_boost_amount: float
    ) -> float | None:
        """Store current volume and increase it by the specified amount."""
        try:
            # Get current media player state
            state = self.hass.states.get(entity_id)
            if not state:
                _LOGGER.warning(
                    "Media player %s not found for volume control", entity_id
                )
                return None

            # Get current volume level
            current_volume = state.attributes.get("volume_level")
            if current_volume is None:
                _LOGGER.warning("Volume level not available for %s", entity_id)
                return None

            _LOGGER.info("Current volume for %s: %.2f", entity_id, current_volume)

            # Calculate new volume (ensure it doesn't exceed 1.0)
            new_volume = min(current_volume + volume_boost_amount, 1.0)

            _LOGGER.info(
                "Increasing volume for %s from %.2f to %.2f (+%.2f)",
                entity_id,
                current_volume,
                new_volume,
                volume_boost_amount,
            )

            # Set the new volume
            await self.hass.services.async_call(
                "media_player",
                "volume_set",
                {
                    "entity_id": entity_id,
                    "volume_level": new_volume,
                },
                blocking=True,
            )

            # Return the original volume for later restoration
            return current_volume

        except Exception as e:
            _LOGGER.error("Failed to boost volume for %s: %s", entity_id, e)
            return None

    async def _schedule_volume_restore(
        self, entity_id: str, original_volume: float, is_sonos: bool = False
    ) -> None:
        """Schedule volume restoration after TTS playback."""
        import asyncio

        # For Sonos, wait longer to account for Sonos-specific behavior
        # For other players, use a shorter delay
        delay = 8.0 if is_sonos else 5.0

        async def restore_volume():
            await asyncio.sleep(delay)
            try:
                _LOGGER.info(
                    "Restoring volume for %s to %.2f", entity_id, original_volume
                )
                await self.hass.services.async_call(
                    "media_player",
                    "volume_set",
                    {
                        "entity_id": entity_id,
                        "volume_level": original_volume,
                    },
                    blocking=True,
                )
                _LOGGER.info("Volume restored successfully for %s", entity_id)
            except Exception as restore_error:
                _LOGGER.warning(
                    "Could not restore volume for %s: %s", entity_id, restore_error
                )

        self.hass.async_create_task(restore_volume())

    async def _handle_audio_recording(
        self, entity_id: str, fields: dict
    ) -> web.Response:
        """Handle audio recording upload and playback using media source."""
        import os
        from datetime import datetime

        audio_data = fields.get("audio")
        if not audio_data:
            return web.json_response({"error": "Missing audio data"}, status=400)

        # Get content type from frontend
        provided_content_type = fields.get("content_type", "audio/webm")

        # Determine file format
        file_extension, media_content_type = self._determine_file_format(
            provided_content_type
        )

        _LOGGER.info(
            "Processing audio upload: %s -> %s", provided_content_type, file_extension
        )

        # Get the media folder path from integration data
        media_folder_path = self.hass.data.get(DOMAIN, {}).get("media_folder_path")
        if not media_folder_path:
            return web.json_response(
                {"error": "Media folder not configured"}, status=500
            )

        # Create unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[
            :-3
        ]  # Include milliseconds
        filename = f"voice_recording_{timestamp}{file_extension}"
        file_path = os.path.join(media_folder_path, filename)

        # Save audio to media folder
        try:
            with open(file_path, "wb") as f:
                f.write(audio_data)
            _LOGGER.info("Saved voice recording to: %s", file_path)
        except Exception as e:
            _LOGGER.error("Failed to save voice recording: %s", e)
            return web.json_response(
                {"error": f"Failed to save recording: {str(e)}"}, status=500
            )

        # Convert WebM to MP3 if needed (updates file in place)
        await self._convert_webm_to_mp3(
            file_path, provided_content_type, file_extension
        )

        # Create media source URI
        media_content_id = (
            f"media-source://media_source/local/voice-recordings/{filename}"
        )

        # Schedule cleanup (optional - keep recordings for 10 minutes)
        await self._schedule_media_file_cleanup(file_path, filename)

        # Get volume control settings
        tts_config = self.hass.data.get(DOMAIN, {}).get("tts_config", {})
        volume_boost_enabled = tts_config.get("volume_boost_enabled", True)
        volume_boost_amount = tts_config.get("volume_boost_amount", 0.1)

        # Store original volume if volume boost is enabled
        original_volume = None
        if volume_boost_enabled:
            original_volume = await self._store_and_boost_volume(
                entity_id, volume_boost_amount
            )

        # Play the audio using media source announcement
        await self._play_media_source_audio(
            entity_id, media_content_id, file_path, original_volume
        )

        return web.json_response({
            "status": "success",
            "message": "Playing audio via media source",
        })

    def _determine_file_format(self, provided_content_type: str) -> tuple[str, str]:
        """Determine file extension and media content type."""
        if "mp4" in provided_content_type:
            return ".m4a", "audio/mp4"
        elif "mpeg" in provided_content_type or "mp3" in provided_content_type:
            return ".mp3", "audio/mpeg"
        elif "wav" in provided_content_type:
            return ".wav", "audio/wav"
        elif "webm" in provided_content_type:
            _LOGGER.info(
                "WebM audio received - converting to MP3 for Sonos compatibility"
            )
            return ".mp3", "audio/mpeg"
        else:
            return ".webm", "audio/webm"

    async def _convert_webm_to_mp3(
        self, temp_path: str, provided_content_type: str, file_extension: str
    ) -> str:
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

    async def _schedule_media_file_cleanup(self, file_path: str, filename: str) -> None:
        """Schedule cleanup of media files after 10 minutes."""
        import asyncio
        import os

        async def cleanup_media_file():
            await asyncio.sleep(600)  # 10 minutes
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                _LOGGER.debug("Cleaned up media file: %s", filename)
            except Exception as cleanup_error:
                _LOGGER.warning("Could not cleanup media file: %s", cleanup_error)

        self.hass.async_create_task(cleanup_media_file())

    async def _play_media_source_audio(
        self,
        entity_id: str,
        media_content_id: str,
        file_path: str,
        original_volume: float | None = None,
    ) -> None:
        """Play audio using media source with announcement mode."""
        _LOGGER.info(
            "Playing audio via media source on %s: %s", entity_id, media_content_id
        )

        try:
            # Use media_player.play_media with announce=True for proper announcement behavior
            await self.hass.services.async_call(
                "media_player",
                "play_media",
                {
                    "entity_id": entity_id,
                    "media_content_id": media_content_id,
                    "media_content_type": "music",
                    "announce": True,
                },
                blocking=True,
            )

            _LOGGER.info("Successfully started media source playback with announcement")

            # Schedule volume restoration if needed
            if original_volume is not None:
                # Get audio duration for proper timing
                restore_delay = await self._get_audio_duration_or_default(file_path)
                await self._schedule_volume_restore_after_delay(
                    entity_id, original_volume, restore_delay
                )

        except Exception as playback_error:
            _LOGGER.error("Failed to play media source audio: %s", playback_error)
            # Restore volume immediately if playback failed
            if original_volume is not None:
                try:
                    await self.hass.services.async_call(
                        "media_player",
                        "volume_set",
                        {
                            "entity_id": entity_id,
                            "volume_level": original_volume,
                        },
                        blocking=True,
                    )
                except Exception as volume_error:
                    _LOGGER.warning(
                        "Could not restore volume after playback error: %s",
                        volume_error,
                    )
            raise

    async def _get_audio_duration_or_default(self, file_path: str) -> float:
        """Get audio file duration or return default value."""
        import os
        import shutil
        import subprocess

        try:
            if os.path.exists(file_path) and shutil.which("ffprobe"):
                result = subprocess.run(
                    [
                        "ffprobe",
                        "-v",
                        "quiet",
                        "-show_entries",
                        "format=duration",
                        "-of",
                        "csv=p=0",
                        file_path,
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                duration = float(result.stdout.strip())
                return max(duration + 1.0, 3.0)
        except Exception as e:
            _LOGGER.debug("Could not determine audio duration: %s", e)

        return 5.0  # Default fallback

    async def _schedule_volume_restore_after_delay(
        self, entity_id: str, original_volume: float, delay: float
    ) -> None:
        """Schedule volume restoration after a specific delay."""
        import asyncio

        async def restore_volume_delayed():
            await asyncio.sleep(delay)
            try:
                _LOGGER.info(
                    "Restoring volume for %s to %.2f", entity_id, original_volume
                )
                await self.hass.services.async_call(
                    "media_player",
                    "volume_set",
                    {
                        "entity_id": entity_id,
                        "volume_level": original_volume,
                    },
                    blocking=True,
                )
                _LOGGER.info("Volume restored successfully for %s", entity_id)
            except Exception as restore_error:
                _LOGGER.warning(
                    "Could not restore volume for %s: %s", entity_id, restore_error
                )

        self.hass.async_create_task(restore_volume_delayed())

    async def _is_wyoming_tts(self, tts_entity_id: str) -> bool:
        """Check if a TTS entity is Wyoming-based."""
        try:
            state = self.hass.states.get(tts_entity_id)
            if not state:
                return False

            # Check if it's explicitly a Wyoming entity
            if "wyoming" in tts_entity_id.lower():
                return True

            # Check if it has Wyoming-specific attributes
            supported_options = state.attributes.get("supported_options", [])
            if "speaker" in supported_options:
                return True

            # Check for Wyoming-style integration or platform
            integration = state.attributes.get("integration")
            platform = state.attributes.get("platform")
            if integration == "wyoming" or platform == "wyoming":
                return True

            # Check attribution for Wyoming/Piper
            attribution = state.attributes.get("attribution")
            if attribution and (
                "wyoming" in attribution.lower() or "piper" in attribution.lower()
            ):
                return True

            return False
        except Exception:
            return False


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

            return web.json_response({
                "available": len(tts_services) > 0,
                "services": tts_services,
                "default_service": "speak" if tts_services else None,
            })
        except Exception as e:
            _LOGGER.error("Error getting TTS config: %s", e)
            return web.json_response({"available": False, "error": str(e)})


def register_ui_view(hass: HomeAssistant, target_url: str = None) -> None:
    """Register the API views for backend functionality."""
    hass.http.register_view(VoiceReplayUploadView(hass))
    hass.http.register_view(VoiceReplayMediaPlayersView(hass))
    hass.http.register_view(VoiceReplayTTSConfigView(hass))

    _LOGGER.debug("API views registered - frontend card is in separate repository")
