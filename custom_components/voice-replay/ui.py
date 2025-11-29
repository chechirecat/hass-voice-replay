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

    def _expand_entity_ids(self, entity_id: str) -> list[str]:
        """Expand group entity_id to all member entity_ids.

        If the entity_id is a group with group_members, return all members.
        Otherwise, return the single entity_id in a list.
        """
        state = self.hass.states.get(entity_id)
        if not state:
            _LOGGER.warning("Entity %s not found, using as-is", entity_id)
            return [entity_id]

        # Check if this entity has group_members attribute
        group_members = state.attributes.get("group_members", [])

        # If it has multiple group members, expand to play on all of them
        if group_members and len(group_members) > 1:
            _LOGGER.info(
                "Expanding group %s to %d members: %s",
                entity_id,
                len(group_members),
                group_members,
            )
            return group_members

        # Not a group or single member, return as single-item list
        return [entity_id]

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
            # Expand group entity_id to all member entity_ids
            target_entity_ids = self._expand_entity_ids(entity_id)

            # Get TTS configuration and setup
            tts_config = self.hass.data.get(DOMAIN, {}).get("tts_config", {})
            _LOGGER.info("Retrieved TTS config from hass.data: %s", tts_config)

            # Handle volume boost
            original_volumes = await self._handle_volume_boost(
                target_entity_ids, tts_config
            )

            # Get TTS engine and configuration
            tts_entity, options, normalized_language = await self._setup_tts_engine(
                tts_config
            )

            if not tts_entity:
                return web.json_response(
                    {"error": "No TTS engine available"}, status=400
                )

            # Play TTS on all target entities
            await self._play_tts_on_targets(
                target_entity_ids,
                text,
                tts_entity,
                options,
                normalized_language,
                original_volumes,
            )

            # Return success message
            if len(target_entity_ids) > 1:
                return web.json_response({
                    "status": "success",
                    "message": f"Playing TTS audio via {tts_entity} on {len(target_entity_ids)} speakers",
                })
            else:
                return web.json_response({
                    "status": "success",
                    "message": f"Playing TTS audio via {tts_entity}",
                })

        except Exception as tts_error:
            return await self._handle_tts_error(tts_error, locals())

    async def _handle_volume_boost(
        self, target_entity_ids: list[str], tts_config: dict
    ) -> dict:
        """Handle volume boost for target entities."""
        original_volumes = {}
        volume_boost_enabled = tts_config.get("volume_boost_enabled", True)
        volume_boost_amount = tts_config.get("volume_boost_amount", 0.1)

        if volume_boost_enabled:
            for target_id in target_entity_ids:
                vol = await self._store_and_boost_volume(target_id, volume_boost_amount)
                if vol is not None:
                    original_volumes[target_id] = vol

        return original_volumes

    async def _setup_tts_engine(
        self, tts_config: dict
    ) -> tuple[str | None, dict | None, str]:
        """Setup TTS engine and return configuration."""
        configured_engine = tts_config.get("engine", "auto")
        configured_language = tts_config.get("language", "de_DE")
        configured_voice = tts_config.get("voice")
        configured_speaker = tts_config.get("speaker")

        _LOGGER.info(
            "TTS request - Engine: %s, Language: %s, Voice: %s, Speaker: %s",
            configured_engine,
            configured_language,
            configured_voice,
            configured_speaker,
        )

        # Determine TTS engine
        tts_entity = await self._determine_tts_engine(configured_engine)
        if not tts_entity:
            return None, None, ""

        # Setup voice and speaker options
        options = await self._setup_voice_options(
            tts_entity, configured_voice, configured_speaker
        )

        # Normalize language
        normalized_language = await self._normalize_language_for_engine(
            tts_entity, configured_language
        )
        if normalized_language != configured_language:
            _LOGGER.info(
                "Language normalized: %s -> %s for engine %s",
                configured_language,
                normalized_language,
                tts_entity,
            )

        return tts_entity, options, normalized_language

    async def _determine_tts_engine(self, configured_engine: str) -> str | None:
        """Determine which TTS engine to use."""
        if configured_engine == "auto":
            tts_entity = await self._get_available_tts_engine()
            _LOGGER.info("Auto-detected TTS engine: %s", tts_entity)
            return tts_entity

        # Use configured engine if available
        state = self.hass.states.get(configured_engine)
        if state and state.state != "unavailable":
            _LOGGER.info("Using configured TTS engine: %s", configured_engine)
            return configured_engine

        # Fallback to auto-detect
        _LOGGER.warning(
            "Configured TTS engine %s not available, falling back to auto-detect",
            configured_engine,
        )
        tts_entity = await self._get_available_tts_engine()
        _LOGGER.info("Fallback TTS engine: %s", tts_entity)
        return tts_entity

    async def _setup_voice_options(
        self,
        tts_entity: str,
        configured_voice: str | None,
        configured_speaker: str | None,
    ) -> dict | None:
        """Setup voice and speaker options for TTS."""
        if not configured_voice:
            return None

        available_voices = await self._get_engine_voices(tts_entity)
        if available_voices and configured_voice not in available_voices:
            _LOGGER.warning(
                "Configured voice '%s' not available for engine %s. Available: %s. Using engine default.",
                configured_voice,
                tts_entity,
                available_voices,
            )
            return None

        options = {"voice": configured_voice}

        if configured_speaker:
            options = await self._add_speaker_option(
                options,
                tts_entity,
                configured_speaker,
                configured_voice,
                available_voices,
            )

        return options

    async def _add_speaker_option(
        self,
        options: dict,
        tts_entity: str,
        configured_speaker: str,
        configured_voice: str,
        available_voices: list | None,
    ) -> dict:
        """Add speaker option to TTS options."""
        if await self._is_wyoming_tts(tts_entity):
            options["speaker"] = configured_speaker
            _LOGGER.info(
                "Adding Wyoming Protocol speaker option: %s", configured_speaker
            )
        else:
            # Try combining voice and speaker for non-Wyoming engines
            combined_voice = f"{configured_voice}-{configured_speaker}"
            if combined_voice in (available_voices or []):
                options["voice"] = combined_voice
                _LOGGER.info("Using combined voice-speaker name: %s", combined_voice)
            else:
                _LOGGER.warning(
                    "Speaker '%s' not supported by non-Wyoming engine %s, ignoring",
                    configured_speaker,
                    tts_entity,
                )

        return options

    async def _play_tts_on_targets(
        self,
        target_entity_ids: list[str],
        text: str,
        tts_entity: str,
        options: dict | None,
        normalized_language: str,
        original_volumes: dict,
    ) -> None:
        """Play TTS on all target entities."""
        for target_id in target_entity_ids:
            is_sonos = any(
                keyword in target_id.lower()
                for keyword in ["sonos", "play:1", "play:3", "play:5"]
            )

            # Prepare text for Sonos if needed
            tts_text = await self._prepare_tts_text_for_target(
                target_id, text, tts_entity, is_sonos
            )

            # Create and execute TTS payload
            payload = await self._create_tts_payload(
                tts_entity, target_id, tts_text, normalized_language, options
            )

            await self._execute_tts_call(target_id, payload)

            # Handle post-TTS actions
            await self._handle_post_tts_actions(target_id, original_volumes, is_sonos)

    async def _prepare_tts_text_for_target(
        self, target_id: str, text: str, tts_entity: str, is_sonos: bool
    ) -> str:
        """Prepare TTS text for specific target."""
        if not is_sonos:
            return text

        _LOGGER.info(
            "Detected Sonos speaker %s, preparing message with silence...", target_id
        )

        # Create snapshot first
        try:
            await self.hass.services.async_call(
                "sonos", "snapshot", {"entity_id": target_id}, blocking=True
            )
        except Exception as sonos_prep_error:
            _LOGGER.warning(
                "Could not create Sonos snapshot for %s: %s",
                target_id,
                sonos_prep_error,
            )

        # Add silence or announcement to the beginning of the text
        return await self._prepare_sonos_message(text, tts_entity)

    async def _create_tts_payload(
        self,
        tts_entity: str,
        target_id: str,
        tts_text: str,
        normalized_language: str,
        options: dict | None,
    ) -> dict:
        """Create TTS payload for service call."""
        payload = {
            "entity_id": tts_entity,
            "media_player_entity_id": target_id,
            "message": tts_text,
            "cache": True,
        }

        if normalized_language:
            payload["language"] = normalized_language
            _LOGGER.info("Using normalized language: %s", normalized_language)
        else:
            payload["language"] = "de_DE"
            _LOGGER.warning("No language configured, forcing German (de_DE)")

        if options:
            payload["options"] = options

        return payload

    async def _execute_tts_call(self, target_id: str, payload: dict) -> None:
        """Execute the TTS service call."""
        _LOGGER.info("TTS payload for %s: %s", target_id, payload)
        _LOGGER.info(
            "Calling tts.speak service for %s with payload: %s", target_id, payload
        )

        await self.hass.services.async_call("tts", "speak", payload, blocking=True)

        _LOGGER.info("TTS service call completed successfully for %s", target_id)

    async def _handle_post_tts_actions(
        self, target_id: str, original_volumes: dict, is_sonos: bool
    ) -> None:
        """Handle actions after TTS playback."""
        # Schedule volume restoration if volume boost was enabled
        if target_id in original_volumes:
            await self._schedule_volume_restore(
                target_id, original_volumes[target_id], is_sonos
            )

        # For Sonos, schedule restoration after a delay
        if is_sonos:

            async def restore_sonos(sonos_entity_id: str):
                import asyncio

                await asyncio.sleep(10.0)
                try:
                    await self.hass.services.async_call(
                        "sonos",
                        "restore",
                        {"entity_id": sonos_entity_id},
                        blocking=True,
                    )
                    _LOGGER.info(
                        "Sonos state restored after TTS for %s", sonos_entity_id
                    )
                except Exception as restore_error:
                    _LOGGER.warning(
                        "Could not restore Sonos state for %s: %s",
                        sonos_entity_id,
                        restore_error,
                    )

            self.hass.async_create_task(restore_sonos(target_id))

    async def _handle_tts_error(
        self, tts_error: Exception, context: dict
    ) -> web.Response:
        """Handle TTS errors with specific error messages."""
        error_msg = str(tts_error)
        tts_entity = context.get("tts_entity")
        configured_language = context.get("tts_config", {}).get("language")
        configured_voice = context.get("tts_config", {}).get("voice")

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
        """Prepare TTS message for Sonos with silence via SSML if supported."""
        try:
            # Try to use SSML for silence if the TTS engine supports it
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

            # No SSML support - return text as-is (silence will be handled at conversion level)
            _LOGGER.info(
                "No SSML support, using original text (silence handled at conversion)"
            )
            return text

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

        # Expand group entity_id to all member entity_ids
        target_entity_ids = self._expand_entity_ids(entity_id)

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
            import asyncio

            # Use asyncio to avoid blocking the event loop
            def write_file():
                with open(file_path, "wb") as f:
                    f.write(audio_data)

            await asyncio.get_event_loop().run_in_executor(None, write_file)
            _LOGGER.info("Saved voice recording to: %s", file_path)
        except Exception as e:
            _LOGGER.error("Failed to save voice recording: %s", e)
            return web.json_response(
                {"error": f"Failed to save recording: {str(e)}"}, status=500
            )

        # Convert WebM to MP3 if needed (updates file in place)
        await self._convert_audio_to_mp3(
            file_path, provided_content_type, file_extension
        )

        # Create media source URI
        media_content_id = f"media-source://media_source/local/{filename}"

        # Schedule cleanup (optional - keep recordings for 60 minutes for testing)
        await self._schedule_media_file_cleanup(file_path, filename)

        # Get volume control settings
        tts_config = self.hass.data.get(DOMAIN, {}).get("tts_config", {})
        volume_boost_enabled = tts_config.get("volume_boost_enabled", True)
        volume_boost_amount = tts_config.get("volume_boost_amount", 0.1)

        # Store original volumes for all target entities if volume boost is enabled
        original_volumes = {}
        if volume_boost_enabled:
            for target_id in target_entity_ids:
                vol = await self._store_and_boost_volume(target_id, volume_boost_amount)
                if vol is not None:
                    original_volumes[target_id] = vol

        # Play the audio on all target entities using media source announcement
        for target_id in target_entity_ids:
            original_vol = original_volumes.get(target_id)
            await self._play_media_source_audio(
                target_id, media_content_id, file_path, original_vol
            )

        # Return success message
        if len(target_entity_ids) > 1:
            return web.json_response({
                "status": "success",
                "message": f"Playing audio via media source on {len(target_entity_ids)} speakers",
            })
        else:
            return web.json_response({
                "status": "success",
                "message": "Playing audio via media source",
            })

    def _determine_file_format(self, provided_content_type: str) -> tuple[str, str]:
        """Determine file extension and media content type."""
        if "mp4" in provided_content_type:
            # Convert m4a to MP3 for universal compatibility
            return ".mp3", "audio/mpeg"
        elif "mpeg" in provided_content_type or "mp3" in provided_content_type:
            return ".mp3", "audio/mpeg"
        elif "wav" in provided_content_type:
            return ".wav", "audio/wav"
        elif "webm" in provided_content_type:
            # Convert WebM to MP3 for universal compatibility
            return ".mp3", "audio/mpeg"
        else:
            return ".mp3", "audio/mpeg"  # Default to MP3 for unknown formats

    async def _convert_audio_to_mp3(
        self, temp_path: str, provided_content_type: str, file_extension: str
    ) -> str:
        """Convert WebM or m4a to MP3 for universal media player compatibility."""
        should_convert = (
            "webm" in provided_content_type and file_extension == ".mp3"
        ) or ("mp4" in provided_content_type and file_extension == ".mp3")

        if should_convert:
            import os
            import shutil
            import subprocess

            if shutil.which("ffmpeg"):
                try:
                    # Determine source format for logging
                    if "mp4" in provided_content_type:
                        source_format = "m4a"
                        _LOGGER.info(
                            "Converting m4a to MP3 for universal compatibility"
                        )
                    else:
                        source_format = "webm"
                        _LOGGER.info(
                            "Converting WebM to MP3 for universal compatibility"
                        )

                    # Create temporary file with .tmp extension to avoid conflicts
                    temp_converted_path = temp_path + ".tmp"

                    command = [
                        "ffmpeg",
                        "-hide_banner",
                        "-loglevel",
                        "error",
                        "-i",
                        temp_path,
                        "-ar",
                        "44100",  # Standard sample rate
                        "-ac",
                        "2",  # Stereo output
                        "-b:a",
                        "128k",  # Consistent bitrate
                        "-f",
                        "mp3",
                        "-y",  # Overwrite output file
                        temp_converted_path,
                    ]

                    result = subprocess.run(
                        command,
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    _LOGGER.debug("FFmpeg conversion stdout: %s", result.stdout)
                    _LOGGER.debug("FFmpeg conversion stderr: %s", result.stderr)

                    # Replace original file with converted file
                    os.remove(temp_path)
                    os.rename(temp_converted_path, temp_path)

                    _LOGGER.info(
                        "Successfully converted %s to MP3",
                        source_format,
                    )
                    return "audio/mpeg"
                except subprocess.CalledProcessError as e:
                    _LOGGER.error("FFmpeg conversion failed: %s", e.stderr)
                    return provided_content_type
                except Exception as e:
                    _LOGGER.error("Conversion error: %s", e)
                    return provided_content_type
            else:
                _LOGGER.warning(
                    "FFmpeg not available, cannot convert %s",
                    source_format if "source_format" in locals() else "audio",
                )
                return provided_content_type

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
        import os

        _LOGGER.info(
            "Playing audio via media source on %s: %s", entity_id, media_content_id
        )

        # Add debugging information
        _LOGGER.info(
            "File exists at path: %s = %s", file_path, os.path.exists(file_path)
        )
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            _LOGGER.info("File size: %s bytes", file_size)
            if file_size == 0:
                _LOGGER.warning("Audio file is empty!")

        # Check media player state
        player_state = self.hass.states.get(entity_id)
        if player_state:
            _LOGGER.info(
                "Media player current state: %s, attributes: %s",
                player_state.state,
                dict(player_state.attributes),
            )
        else:
            _LOGGER.warning("Media player %s not found!", entity_id)
            return

        try:
            # Check if this is a Sonos speaker - use direct serving for better reliability
            is_sonos = any(
                keyword in entity_id.lower()
                for keyword in ["sonos", "play:1", "play:3", "play:5"]
            )

            if is_sonos:
                _LOGGER.info(
                    "Detected Sonos speaker - using direct HTTP serving for better reliability"
                )
                await self._play_with_direct_serving(
                    entity_id, file_path, original_volume
                )
                return

            # For non-Sonos players, try media source first
            _LOGGER.info("Attempting media source playback with announcement...")
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

            _LOGGER.info("Media source playback call completed, checking state...")

            # Give it a moment to start playing
            import asyncio

            await asyncio.sleep(1.0)

            # Check new state
            new_state = self.hass.states.get(entity_id)
            if new_state:
                _LOGGER.info(
                    "Media player state after playback: %s, media_title: %s",
                    new_state.state,
                    new_state.attributes.get("media_title"),
                )
                _LOGGER.info(
                    "Current media_content_id: %s",
                    new_state.attributes.get("media_content_id"),
                )

            # Check if playback actually started by comparing media_content_id
            if new_state and media_content_id in str(
                new_state.attributes.get("media_content_id", "")
            ):
                _LOGGER.info("Media source playback successful!")
            else:
                _LOGGER.warning(
                    "Media source playback failed (content didn't change), trying direct HTTP serving..."
                )
                await self._play_with_direct_serving(
                    entity_id, file_path, original_volume
                )
                return

            _LOGGER.info("Successfully started media source playback")

            # Schedule volume restoration if needed
            if original_volume is not None:
                # Get audio duration for proper timing
                restore_delay = await self._get_audio_duration_or_default(file_path)
                await self._schedule_volume_restore_after_delay(
                    entity_id, original_volume, restore_delay
                )

        except Exception as playback_error:
            _LOGGER.error(
                "Media source playback failed: %s", playback_error, exc_info=True
            )
            _LOGGER.info("Falling back to direct HTTP serving...")
            try:
                await self._play_with_direct_serving(
                    entity_id, file_path, original_volume
                )
            except Exception as fallback_error:
                _LOGGER.error(
                    "Fallback playback also failed: %s", fallback_error, exc_info=True
                )
                # Restore volume immediately if all playback failed
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

    async def _play_with_direct_serving(
        self,
        entity_id: str,
        file_path: str,
        original_volume: float | None = None,
    ) -> None:
        """Play audio using direct HTTP serving as fallback."""
        import os

        filename = os.path.basename(file_path)

        # Create direct URL using Home Assistant's built-in media serving
        external_url = self.hass.config.external_url or "http://localhost:8123"
        builtin_media_url = f"{external_url}/media/local/{filename}"

        _LOGGER.info("Playing audio via direct HTTP serving")
        _LOGGER.info("Built-in HA media URL: %s", builtin_media_url)

        # Determine content type
        if filename.endswith(".mp3"):
            content_type = "audio/mpeg"
        elif filename.endswith(".wav"):
            content_type = "audio/wav"
        elif filename.endswith(".m4a"):
            content_type = "audio/mp4"
        else:
            content_type = "audio/mpeg"

        # Check if this is a Sonos speaker
        is_sonos = any(
            keyword in entity_id.lower()
            for keyword in ["sonos", "play:1", "play:3", "play:5"]
        )

        if is_sonos:
            await self._handle_sonos_direct_playback(
                entity_id, builtin_media_url, content_type, file_path, original_volume
            )
        else:
            # For non-Sonos players, use standard approach with announce
            await self.hass.services.async_call(
                "media_player",
                "play_media",
                {
                    "entity_id": entity_id,
                    "media_content_id": builtin_media_url,
                    "media_content_type": content_type,
                    "announce": True,
                },
                blocking=True,
            )

            # Schedule volume restoration
            if original_volume is not None:
                restore_delay = await self._get_audio_duration_or_default(file_path)
                await self._schedule_volume_restore_after_delay(
                    entity_id, original_volume, restore_delay
                )

    async def _handle_sonos_direct_playback(
        self,
        entity_id: str,
        media_url: str,
        content_type: str,
        file_path: str,
        original_volume: float | None = None,
    ) -> None:
        """Handle Sonos-specific direct playback with snapshot/restore."""
        import asyncio

        # Create snapshot
        try:
            _LOGGER.info("Creating Sonos snapshot before playing voice message")
            await self.hass.services.async_call(
                "sonos",
                "snapshot",
                {"entity_id": entity_id},
                blocking=True,
            )
            await asyncio.sleep(0.2)
        except Exception as snapshot_error:
            _LOGGER.warning("Could not create Sonos snapshot: %s", snapshot_error)

        # Try to play the audio
        success = await self._play_on_sonos_direct(entity_id, media_url, content_type)
        if not success:
            raise Exception("All Sonos content types failed")

        # Schedule restoration
        restore_delay = await self._get_audio_duration_or_default(file_path)
        await self._schedule_sonos_restore_direct(
            entity_id, restore_delay, original_volume
        )

    async def _play_on_sonos_direct(
        self, entity_id: str, media_url: str, content_type: str
    ) -> bool:
        """Try to play on Sonos with different content types."""
        # Try multiple content types that work with Sonos URL streaming
        sonos_content_types = [
            content_type,  # Try the detected type first
            "audio/mpeg",
            "audio/mp3",
            "audio/x-mpeg",
            "audio/x-mp3",
            "music",
            "application/octet-stream",
        ]

        for sonos_type in sonos_content_types:
            try:
                _LOGGER.info(
                    "Trying Sonos direct streaming with content type: %s", sonos_type
                )
                await self.hass.services.async_call(
                    "media_player",
                    "play_media",
                    {
                        "entity_id": entity_id,
                        "media_content_id": media_url,
                        "media_content_type": sonos_type,
                    },
                    blocking=True,
                )
                _LOGGER.info("Successfully started Sonos playback with: %s", sonos_type)
                return True
            except Exception as sonos_error:
                _LOGGER.warning(
                    "Sonos content type %s failed: %s", sonos_type, sonos_error
                )
                continue

        return False

    async def _schedule_sonos_restore_direct(
        self, entity_id: str, delay: float, original_volume: float | None = None
    ) -> None:
        """Schedule Sonos state restoration after direct playback."""
        import asyncio

        async def restore_sonos():
            await asyncio.sleep(delay)
            try:
                await self.hass.services.async_call(
                    "sonos",
                    "restore",
                    {"entity_id": entity_id},
                    blocking=True,
                )
                _LOGGER.info("Sonos state restored successfully")

                # Also restore volume if needed
                if original_volume is not None:
                    try:
                        _LOGGER.info(
                            "Restoring Sonos volume to %.2f",
                            original_volume,
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
                        _LOGGER.info("Sonos volume restored successfully")
                    except Exception as volume_error:
                        _LOGGER.warning(
                            "Could not restore Sonos volume: %s",
                            volume_error,
                        )

            except Exception as restore_error:
                _LOGGER.warning("Could not restore Sonos state: %s", restore_error)

        self.hass.async_create_task(restore_sonos())

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
        """Return list of available media players with Sonos groups at the top."""
        media_players = []
        sonos_groups = []
        individual_players = []

        _LOGGER.info("Processing media players request...")

        # First pass: collect all media players and identify Sonos entities
        for state in self.hass.states.async_all():
            if state.entity_id.startswith("media_player."):
                player_info = {
                    "entity_id": state.entity_id,
                    "name": state.attributes.get("friendly_name", state.entity_id),
                    "state": state.state,
                    "is_sonos": self._is_sonos_entity(state),
                    "group_members": state.attributes.get("group_members", []),
                    "device_class": state.attributes.get("device_class"),
                }

                # Check if this is a Sonos group coordinator
                if (
                    player_info["is_sonos"]
                    and len(player_info["group_members"]) > 1
                    and state.entity_id in player_info["group_members"]
                ):
                    # This is a Sonos group coordinator
                    group_info = player_info.copy()
                    group_info["name"] = (
                        f"🔊 {player_info['name']} Group ({len(player_info['group_members'])} speakers)"
                    )
                    group_info["is_group"] = True
                    sonos_groups.append(group_info)
                    _LOGGER.debug(
                        "Added Sonos group: %s (%s) with %d members",
                        group_info["name"],
                        group_info["entity_id"],
                        len(player_info["group_members"]),
                    )

                # Add to individual players list
                individual_players.append(player_info)
                _LOGGER.debug(
                    "Added media player: %s (%s) - %s %s",
                    player_info["name"],
                    player_info["entity_id"],
                    player_info["state"],
                    "(Sonos)" if player_info["is_sonos"] else "",
                )

        # Sort groups and individual players alphabetically by name
        sonos_groups.sort(key=lambda x: x["name"].lower())
        individual_players.sort(key=lambda x: x["name"].lower())

        # Combine: Sonos groups first, then individual players
        media_players = sonos_groups + individual_players

        _LOGGER.info(
            "Found %d media players total (%d Sonos groups, %d individual players)",
            len(media_players),
            len(sonos_groups),
            len(individual_players),
        )
        _LOGGER.debug("Returning media players: %s", [p["name"] for p in media_players])

        return web.json_response(media_players)

    def _is_sonos_entity(self, state) -> bool:
        """Check if the media player entity is a Sonos device."""
        # Check if entity is from Sonos integration
        integration = state.attributes.get("integration")
        if integration == "sonos":
            return True

        # Check device class
        device_class = state.attributes.get("device_class")
        if device_class == "speaker":
            # Additional check for Sonos-specific attributes
            return (
                "group_members" in state.attributes
                or "sonos" in state.entity_id.lower()
                or "sonos" in state.attributes.get("friendly_name", "").lower()
            )

        return False


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
            # Get TTS configuration from integration data
            tts_config = self.hass.data.get(DOMAIN, {}).get("tts_config", {})

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
                "prepend_silence_seconds": tts_config.get("prepend_silence_seconds", 3),
                "volume_boost_enabled": tts_config.get("volume_boost_enabled", True),
                "volume_boost_amount": tts_config.get("volume_boost_amount", 0.1),
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
