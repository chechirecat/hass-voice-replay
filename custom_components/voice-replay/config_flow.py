"""Config flow for Voice Replay."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class VoiceReplayFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Voice Replay."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="Voice Replay", data=user_input)

        # No configuration needed for native UI
        data_schema = vol.Schema({})

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return VoiceReplayOptionsFlowHandler(config_entry)


class VoiceReplayOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Voice Replay options flow."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry
        self._current_config = dict(config_entry.options)

    async def async_step_init(self, user_input=None):
        """Manage all TTS configuration in a single step."""
        errors = {}

        if user_input is not None:
            # Parse combined voice-speaker selection if present
            combined_voice = user_input.get("tts_voice_combined")
            if combined_voice:
                voice, speaker = self._parse_combined_voice_value(combined_voice)
                user_input["tts_voice"] = voice
                user_input["tts_speaker"] = speaker

            # Validate the configuration
            selected_engine = user_input.get("tts_engine", "auto")
            selected_language = user_input.get("tts_language", "de_DE")
            selected_voice = user_input.get("tts_voice")
            selected_speaker = user_input.get("tts_speaker")

            # Validate voice if specified
            if selected_voice and selected_engine != "auto":
                available_voices = await self._get_engine_voices_for_language(
                    selected_engine, selected_language
                )
                if available_voices and selected_voice not in available_voices:
                    errors["tts_voice_combined"] = "voice_not_available"

            # Validate speaker if specified
            if selected_speaker and selected_voice and selected_engine != "auto":
                is_valid = await self._validate_voice_speaker_combination(
                    selected_engine, selected_voice, selected_speaker
                )
                if not is_valid:
                    errors["tts_voice_combined"] = "speaker_not_available"

            if not errors:
                # Remove the combined field from the final data
                final_data = dict(user_input)
                final_data.pop("tts_voice_combined", None)
                return self.async_create_entry(title="", data=final_data)

        # Get current settings
        current_engine = self.config_entry.options.get("tts_engine", "auto")
        current_language = self.config_entry.options.get("tts_language", "de_DE")
        current_voice = self.config_entry.options.get("tts_voice")
        current_speaker = self.config_entry.options.get("tts_speaker")
        current_sonos_mode = self.config_entry.options.get(
            "sonos_announcement_mode", "silence"
        )

        # Get available options
        tts_engines = await self._get_tts_engines()
        available_languages = await self._get_engine_languages(current_engine)

        # Get combined voice-speaker options
        combined_voice_options = await self._get_combined_voice_options(
            current_engine, current_language
        )

        # Determine current combined voice value
        current_combined_voice = None
        if current_voice:
            if current_speaker:
                current_combined_voice = f"{current_voice}|{current_speaker}"
            else:
                current_combined_voice = current_voice

        # Build comprehensive schema
        data_schema_dict = {}

        # Engine selection
        data_schema_dict[vol.Optional("tts_engine", default=current_engine)] = (
            selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=tts_engines,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        )

        # Language selection
        if available_languages:
            language_options = []
            for lang in available_languages:
                label = self._format_language_label(lang)
                language_options.append({"value": lang, "label": label})
        else:
            # Default language options
            language_options = [
                {"value": "de_DE", "label": "German (de_DE)"},
                {"value": "de", "label": "German (de)"},
                {"value": "en_US", "label": "English US (en_US)"},
                {"value": "en", "label": "English (en)"},
                {"value": "fr", "label": "French (fr)"},
                {"value": "es", "label": "Spanish (es)"},
                {"value": "it", "label": "Italian (it)"},
            ]

        data_schema_dict[vol.Optional("tts_language", default=current_language)] = (
            selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=language_options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        )

        # Combined Voice and Speaker selection
        if combined_voice_options:
            data_schema_dict[
                vol.Optional("tts_voice_combined", default=current_combined_voice)
            ] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=combined_voice_options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        else:
            # Fallback to text input if no voices detected
            data_schema_dict[
                vol.Optional("tts_voice_combined", default=current_combined_voice or "")
            ] = selector.TextSelector()

        # Sonos announcement options
        locale = (
            self.hass.config.language if hasattr(self.hass.config, "language") else "en"
        )

        if locale.startswith("de"):
            sonos_options = [
                {"value": "silence", "label": "3 Sekunden Stille"},
                {"value": "announcement", "label": "Sprachansage (Achtung...)"},
                {
                    "value": "disabled",
                    "label": "Keine Ansage (schneller, aber möglicherweise abgeschnitten)",
                },
            ]
        else:
            sonos_options = [
                {"value": "silence", "label": "3 second silence"},
                {"value": "announcement", "label": "Verbal announcement (Achtung...)"},
                {
                    "value": "disabled",
                    "label": "No announcement (faster but may cut off)",
                },
            ]

        data_schema_dict[
            vol.Optional("sonos_announcement_mode", default=current_sonos_mode)
        ] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=sonos_options,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )

        data_schema = vol.Schema(data_schema_dict)

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "engine": current_engine,
                "language": current_language,
                "voice_count": str(len(combined_voice_options))
                if combined_voice_options
                else "0",
                "speaker_count": "auto-detected",  # Speakers are now included in voice options
            },
        )

    async def _get_tts_engines(self) -> list[dict]:
        """Get available TTS engines."""
        engines = []

        # Add "Auto-detect" option
        engines.append({"value": "auto", "label": "Auto-detect"})

        # Get all available TTS entities
        for state in self.hass.states.async_all():
            if state.entity_id.startswith("tts.") and state.state != "unavailable":
                friendly_name = state.attributes.get("friendly_name", state.entity_id)
                engines.append({"value": state.entity_id, "label": friendly_name})

        return engines

    async def _get_engine_languages(self, engine_entity_id: str) -> list[str]:
        """Get available languages for a TTS engine."""
        if engine_entity_id == "auto":
            return []

        try:
            state = self.hass.states.get(engine_entity_id)
            if not state:
                return []

            # Method 1: Check for supported_languages attribute
            languages = state.attributes.get(
                "supported_languages"
            ) or state.attributes.get("languages")
            if languages and isinstance(languages, (list, tuple)):
                return list(languages)

            # Method 2: For Piper TTS, check for voice attributes that indicate languages
            # Piper often has attributes like "voices_de_DE", "voices_en_US", etc.
            if (
                "piper" in engine_entity_id.lower()
                or "wyoming" in engine_entity_id.lower()
            ):
                piper_languages = []
                for attr_name in state.attributes:
                    if attr_name.startswith("voices_"):
                        # Extract language from "voices_de_DE" -> "de_DE"
                        lang_code = attr_name.replace("voices_", "")
                        if lang_code and lang_code not in piper_languages:
                            piper_languages.append(lang_code)
                if piper_languages:
                    # Debug logging to see what languages we found
                    _LOGGER.info(
                        "Found Piper/Wyoming languages for %s: %s",
                        engine_entity_id,
                        piper_languages,
                    )
                    return sorted(piper_languages)

                # Alternative method for Wyoming: check supported_languages
                if hasattr(state, "entity") and hasattr(
                    state.entity, "supported_languages"
                ):
                    return list(state.entity.supported_languages)

                # Check for voice information in supported_voices attribute
                supported_voices = state.attributes.get("supported_voices")
                if supported_voices and isinstance(supported_voices, dict):
                    # supported_voices might be structured like {"en-US": [...], "de-DE": [...]}
                    return sorted(supported_voices.keys())

            # Method 3: Check if voices attribute contains language info
            voices = state.attributes.get("voices") or state.attributes.get(
                "available_voices"
            )
            if voices and isinstance(voices, (list, tuple)):
                # Try to extract unique languages from voice names
                # Voice names might be like "de_DE-eva-low" or similar
                detected_languages = set()
                for voice in voices:
                    if isinstance(voice, str):
                        # Look for language patterns in voice names
                        parts = voice.split("-")
                        if len(parts) > 0:
                            first_part = parts[0]
                            # Check if it looks like a language code
                            if "_" in first_part or (
                                len(first_part) == 2 and first_part.isalpha()
                            ):
                                detected_languages.add(first_part)
                if detected_languages:
                    return sorted(detected_languages)

        except Exception:
            pass
        return []

    async def _get_engine_voices_for_language(
        self, engine_entity_id: str, language: str
    ) -> list[str]:
        """Get available voices for a TTS engine and specific language."""
        if engine_entity_id == "auto":
            return []

        try:
            state = self.hass.states.get(engine_entity_id)
            if not state:
                return []

            # Method 1: Check for language-specific voices (e.g., voices_de, voices_en)
            lang_voices_key = f"voices_{language}"
            lang_voices = state.attributes.get(lang_voices_key)
            if lang_voices and isinstance(lang_voices, (list, tuple)):
                return list(lang_voices)

            # Method 2: For Wyoming TTS entities, check supported_voices attribute
            if (
                "wyoming" in engine_entity_id.lower()
                or "piper" in engine_entity_id.lower()
            ):
                supported_voices = state.attributes.get("supported_voices")
                if supported_voices and isinstance(supported_voices, dict):
                    # supported_voices might be {"en-US": [voice1, voice2], "de-DE": [...]}
                    lang_voices = supported_voices.get(language, [])
                    if lang_voices:
                        return list(lang_voices)

                    # Try alternative language formats
                    for lang_key in supported_voices:
                        if (
                            language.lower() in lang_key.lower()
                            or lang_key.lower() in language.lower()
                        ):
                            return list(supported_voices[lang_key])

                # Check for Wyoming-style voice enumeration via async_get_supported_voices
                # This should be available on Wyoming TTS entities
                try:
                    # Try to get the TTS entity directly
                    tts_entities = self.hass.data.get("tts", {})
                    if hasattr(tts_entities, "get_entity"):
                        entity = tts_entities.get_entity(engine_entity_id)
                        if entity and hasattr(entity, "async_get_supported_voices"):
                            voices = entity.async_get_supported_voices(language)
                            if voices:
                                return [voice.voice_id for voice in voices]
                except Exception:
                    pass

            # Method 3: Check for general voices attribute and filter by language
            all_voices = state.attributes.get("voices") or state.attributes.get(
                "available_voices"
            )
            if all_voices and isinstance(all_voices, (list, tuple)):
                # Try to filter voices that contain the language code
                filtered_voices = [
                    voice for voice in all_voices if language in voice.lower()
                ]
                if filtered_voices:
                    return filtered_voices
                # If no language-specific filtering worked, return all voices
                return list(all_voices)

            # Method 4: Check for voice_languages mapping
            voice_languages = state.attributes.get("voice_languages", {})
            if isinstance(voice_languages, dict) and language in voice_languages:
                return voice_languages[language]

        except Exception:
            pass
        return []

    def _format_language_label(self, lang_code: str) -> str:
        """Format language code into a user-friendly label."""
        # Common language mappings
        lang_map = {
            "de": "German",
            "de-DE": "German (Germany)",
            "de_DE": "German (Germany)",
            "en": "English",
            "en-US": "English (US)",
            "en-GB": "English (UK)",
            "en_US": "English (US)",
            "en_GB": "English (UK)",
            "fr": "French",
            "fr-FR": "French (France)",
            "fr_FR": "French (France)",
            "es": "Spanish",
            "es-ES": "Spanish (Spain)",
            "es_ES": "Spanish (Spain)",
            "it": "Italian",
            "it-IT": "Italian (Italy)",
            "it_IT": "Italian (Italy)",
        }

        friendly_name = lang_map.get(lang_code, lang_code.upper())
        return f"{friendly_name} ({lang_code})"

    async def _get_combined_voice_options(
        self, engine_entity_id: str, language: str
    ) -> list[dict]:
        """Get combined voice-speaker options in human-readable format."""
        if engine_entity_id == "auto":
            return []

        # Get all available voices for the language
        available_voices = await self._get_engine_voices_for_language(
            engine_entity_id, language
        )

        combined_options = []

        for voice in available_voices:
            # Try to get speakers for this voice
            speakers = await self._get_voice_speakers(engine_entity_id, voice)

            if speakers:
                # Create combined options for each speaker
                for speaker in speakers:
                    # Create human-readable label
                    display_name = self._format_voice_display_name(voice, speaker)
                    # Store both voice and speaker in the value as a special format
                    combined_value = f"{voice}|{speaker}"
                    combined_options.append({
                        "value": combined_value,
                        "label": display_name,
                    })
            else:
                # No speakers, just use the voice name
                display_name = self._format_voice_display_name(voice, None)
                combined_options.append({
                    "value": voice,  # Just the voice, no separator
                    "label": display_name,
                })

        return combined_options

    def _format_voice_display_name(self, voice: str, speaker: str | None) -> str:
        """Format voice and speaker into human-readable display name."""
        # Parse voice name structure: "language-speakername-pitch"
        if "-" in voice:
            parts = voice.split("-")

            if len(parts) >= 3:
                # Expected format: ["de_DE", "thorsten", "low"]
                # Skip first part (language), use middle part(s) as speaker, last part as pitch
                pitch_part = parts[-1]
                speaker_parts = parts[1:-1]  # Everything between language and pitch

                # Format speaker name: capitalize each word
                if speaker_parts:
                    formatted_speaker = " ".join(
                        part.capitalize() for part in speaker_parts
                    )
                    return f"{formatted_speaker} ({pitch_part})"

            elif len(parts) == 2:
                # Format might be "speakername-pitch" without language
                speaker_part = parts[0]
                pitch_part = parts[1]

                # Check if first part looks like a language code
                if len(speaker_part) <= 5 and (
                    "_" in speaker_part or speaker_part.isupper()
                ):
                    # Likely a language code, treat second part as speaker name
                    return parts[1].capitalize()
                else:
                    # First part is speaker, second is pitch
                    formatted_speaker = speaker_part.capitalize()
                    return f"{formatted_speaker} ({pitch_part})"

        # If no dashes or unexpected format, try to extract from underscores
        if "_" in voice:
            # Handle formats like "de_DE_thorsten_low"
            parts = voice.split("_")
            if len(parts) >= 3:
                # Skip language parts, use the rest
                non_language_parts = []
                for part in parts:
                    # Skip obvious language codes (2 letters, all caps)
                    if not (len(part) <= 2 and part.isupper()):
                        non_language_parts.append(part)

                if len(non_language_parts) >= 2:
                    # Last part is likely pitch, everything else is speaker
                    speaker_parts = non_language_parts[:-1]
                    pitch_part = non_language_parts[-1]
                    formatted_speaker = " ".join(
                        part.capitalize() for part in speaker_parts
                    )
                    return f"{formatted_speaker} ({pitch_part})"
                elif len(non_language_parts) == 1:
                    return non_language_parts[0].capitalize()

        # Fallback: return the original voice name, formatted
        return voice.replace("_", " ").replace("-", " ").title()

    def _parse_combined_voice_value(
        self, combined_value: str
    ) -> tuple[str, str | None]:
        """Parse combined voice value back into voice and speaker components."""
        if "|" in combined_value:
            # Split the combined value
            voice, speaker = combined_value.split("|", 1)
            return voice, speaker
        else:
            # No speaker, just voice
            return combined_value, None

    async def _get_voice_speakers(
        self, engine_entity_id: str, voice_name: str
    ) -> list[str]:
        """Get available speakers for a specific voice in a TTS engine."""
        if engine_entity_id == "auto" or not voice_name:
            return []

        try:
            state = self.hass.states.get(engine_entity_id)
            if not state:
                return []

            # Method 1: Check for Wyoming Protocol speaker attributes
            # Wyoming/Piper often stores speakers in voice-specific attributes
            voice_speakers_key = f"speakers_{voice_name}"
            voice_speakers = state.attributes.get(voice_speakers_key)
            if voice_speakers and isinstance(voice_speakers, (list, tuple)):
                return list(voice_speakers)

            # Method 2: Check for general speakers attribute
            all_speakers = state.attributes.get("speakers") or state.attributes.get(
                "available_speakers"
            )
            if all_speakers and isinstance(all_speakers, (list, tuple)):
                return list(all_speakers)

            # Method 3: Check if the voice name contains speaker information
            # For Piper voices like "de_DE-thorsten-low", the speaker might be "thorsten"
            if "-" in voice_name:
                parts = voice_name.split("-")
                if len(parts) >= 2:
                    # Try different patterns:
                    # Format 1: language-speaker-quality (e.g., "de_DE-thorsten-low")
                    # Format 2: speaker-quality (e.g., "thorsten-low")
                    potential_speakers = []

                    # Check if first part looks like language code
                    first_part = parts[0]
                    if "_" in first_part or len(first_part) == 2:
                        # Likely language-speaker-quality format
                        if len(parts) >= 2:
                            potential_speakers.append(parts[1])  # thorsten
                    else:
                        # Likely speaker-quality format
                        potential_speakers.append(parts[0])  # speaker name

                    # Also try extracting speaker names that aren't just quality indicators
                    for part in parts[1:]:  # Skip the first part (likely language)
                        if part not in ["low", "medium", "high", "x_low", "x-low"]:
                            potential_speakers.append(part)

                    # Remove duplicates and return
                    unique_speakers = list(set(potential_speakers))
                    if unique_speakers:
                        _LOGGER.debug(
                            "Extracted speakers from voice name '%s': %s",
                            voice_name,
                            unique_speakers,
                        )
                        return unique_speakers

            # Method 4: Check for voice-specific speaker mappings
            voice_speaker_mapping = state.attributes.get("voice_speakers", {})
            if (
                isinstance(voice_speaker_mapping, dict)
                and voice_name in voice_speaker_mapping
            ):
                speakers = voice_speaker_mapping[voice_name]
                if isinstance(speakers, (list, tuple)):
                    return list(speakers)
                elif isinstance(speakers, str):
                    return [speakers]

            # Method 5: For Wyoming TTS, check supported_options for speaker capability
            supported_options = state.attributes.get("supported_options", [])
            if "speaker" in supported_options:
                # If speaker is supported but no specific speakers listed,
                # this might be a multi-speaker voice - return empty to show text input
                return []

        except Exception as e:
            _LOGGER.warning(
                "Error getting speakers for voice %s in engine %s: %s",
                voice_name,
                engine_entity_id,
                e,
            )
        return []

    async def _validate_voice_speaker_combination(
        self, engine_entity_id: str, voice_name: str, speaker_name: str
    ) -> bool:
        """Validate that a voice and speaker combination is valid for the engine."""
        if engine_entity_id == "auto" or not voice_name:
            return True  # Skip validation for auto-detect

        try:
            # For Wyoming TTS, check if the speaker is valid for the voice
            if (
                "wyoming" in engine_entity_id.lower()
                or "piper" in engine_entity_id.lower()
            ):
                available_speakers = await self._get_voice_speakers(
                    engine_entity_id, voice_name
                )
                if available_speakers and speaker_name:
                    return speaker_name in available_speakers
                # If no speakers listed but speaker provided, assume it might be valid
                return True

            # For other engines, check if combined voice-speaker exists
            if speaker_name:
                available_voices = await self._get_engine_voices_for_language(
                    engine_entity_id, self._current_config.get("tts_language", "de")
                )
                combined_name = f"{voice_name}-{speaker_name}"
                return combined_name in (available_voices or [])

            return True
        except Exception as e:
            _LOGGER.warning(
                "Error validating voice-speaker combination %s-%s for engine %s: %s",
                voice_name,
                speaker_name,
                engine_entity_id,
                e,
            )
            return True  # Assume valid if validation fails

    async def _is_wyoming_engine(self, engine_entity_id: str) -> bool:
        """Check if an engine is Wyoming-based."""
        if engine_entity_id == "auto":
            return False

        try:
            state = self.hass.states.get(engine_entity_id)
            if not state:
                return False

            # Check various indicators of Wyoming TTS
            if "wyoming" in engine_entity_id.lower():
                return True

            supported_options = state.attributes.get("supported_options", [])
            if "speaker" in supported_options:
                return True

            integration = state.attributes.get("integration")
            platform = state.attributes.get("platform")
            if integration == "wyoming" or platform == "wyoming":
                return True

            return False
        except Exception:
            return False
