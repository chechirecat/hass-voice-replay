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
        """Manage the TTS engine selection."""
        errors = {}

        if user_input is not None:
            self._current_config.update(user_input)
            # If engine was selected, go to language step
            if "tts_engine" in user_input:
                return await self.async_step_language()
            return self.async_create_entry(title="", data=self._current_config)

        # Get available TTS engines
        tts_engines = await self._get_tts_engines()

        # Get current engine setting
        current_tts_engine = self.config_entry.options.get("tts_engine", "auto")

        # Build schema for engine selection
        data_schema = vol.Schema({
            vol.Optional("tts_engine", default=current_tts_engine): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=tts_engines,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={},
        )

    async def async_step_language(self, user_input=None):
        """Manage the language selection."""
        errors = {}

        if user_input is not None:
            self._current_config.update(user_input)
            # If language was selected, go to voice step
            if "tts_language" in user_input:
                return await self.async_step_voice()
            return self.async_create_entry(title="", data=self._current_config)

        # Get available languages for selected engine
        selected_engine = self._current_config.get("tts_engine", "auto")
        available_languages = await self._get_engine_languages(selected_engine)

        # Get current language setting
        current_language = self.config_entry.options.get("tts_language", "de_DE")

        # Build language options
        language_options = []
        if available_languages:
            # Use engine-specific languages
            for lang in available_languages:
                # Create a more user-friendly label
                label = self._format_language_label(lang)
                language_options.append({"value": lang, "label": label})
        else:
            # Default language options with common formats
            language_options = [
                {"value": "de_DE", "label": "German (de_DE)"},
                {"value": "de", "label": "German (de)"},
                {"value": "en_US", "label": "English US (en_US)"},
                {"value": "en", "label": "English (en)"},
                {"value": "fr", "label": "French (fr)"},
                {"value": "es", "label": "Spanish (es)"},
                {"value": "it", "label": "Italian (it)"},
            ]

        data_schema = vol.Schema({
            vol.Optional("tts_language", default=current_language): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=language_options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
        })

        return self.async_show_form(
            step_id="language",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={"engine": selected_engine},
        )

    async def async_step_voice(self, user_input=None):
        """Manage the voice selection."""
        errors = {}

        if user_input is not None:
            self._current_config.update(user_input)
            return self.async_create_entry(title="", data=self._current_config)

        # Get available voices for selected engine and language
        selected_engine = self._current_config.get("tts_engine", "auto")
        selected_language = self._current_config.get("tts_language", "de")
        available_voices = await self._get_engine_voices_for_language(selected_engine, selected_language)

        # Get current voice setting
        current_voice = self.config_entry.options.get("tts_voice")

        data_schema_dict = {}

        if available_voices:
            voice_options = [{"value": voice, "label": voice} for voice in available_voices]
            data_schema_dict[vol.Optional("tts_voice", default=current_voice)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=voice_options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        else:
            # No voices available - show text input for manual entry
            data_schema_dict[vol.Optional("tts_voice", default=current_voice or "")] = selector.TextSelector()

        # Add Sonos announcement options
        current_sonos_mode = self.config_entry.options.get("sonos_announcement_mode", "silence")

        # Get localized option labels (fallback to English if translation not available)
        locale = self.hass.config.language if hasattr(self.hass.config, 'language') else 'en'

        if locale.startswith('de'):
            # German labels
            sonos_options = [
                {"value": "silence", "label": "3 Sekunden Stille"},
                {"value": "announcement", "label": "Sprachansage (Achtung...)"},
                {"value": "disabled", "label": "Keine Ansage (schneller, aber möglicherweise abgeschnitten)"},
            ]
        else:
            # English labels (default)
            sonos_options = [
                {"value": "silence", "label": "3 second silence"},
                {"value": "announcement", "label": "Verbal announcement (Achtung...)"},
                {"value": "disabled", "label": "No announcement (faster but may cut off)"},
            ]

        data_schema_dict[vol.Optional("sonos_announcement_mode", default=current_sonos_mode)] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=sonos_options,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )

        data_schema = vol.Schema(data_schema_dict)

        return self.async_show_form(
            step_id="voice",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "engine": selected_engine,
                "language": selected_language,
                "voice_count": str(len(available_voices)) if available_voices else "0"
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
            languages = state.attributes.get("supported_languages") or state.attributes.get("languages")
            if languages and isinstance(languages, (list, tuple)):
                return list(languages)

            # Method 2: For Piper TTS, check for voice attributes that indicate languages
            # Piper often has attributes like "voices_de_DE", "voices_en_US", etc.
            if "piper" in engine_entity_id.lower():
                piper_languages = []
                for attr_name in state.attributes:
                    if attr_name.startswith("voices_"):
                        # Extract language from "voices_de_DE" -> "de_DE"
                        lang_code = attr_name.replace("voices_", "")
                        if lang_code and lang_code not in piper_languages:
                            piper_languages.append(lang_code)
                if piper_languages:
                    # Debug logging to see what languages we found
                    _LOGGER.info("Found Piper languages for %s: %s", engine_entity_id, piper_languages)
                    return sorted(piper_languages)

            # Method 3: Check if voices attribute contains language info
            voices = state.attributes.get("voices") or state.attributes.get("available_voices")
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
                            if "_" in first_part or (len(first_part) == 2 and first_part.isalpha()):
                                detected_languages.add(first_part)
                if detected_languages:
                    return sorted(detected_languages)

        except Exception:
            pass
        return []

    async def _get_engine_voices_for_language(self, engine_entity_id: str, language: str) -> list[str]:
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

            # Method 2: Check for general voices attribute and filter by language
            all_voices = state.attributes.get("voices") or state.attributes.get("available_voices")
            if all_voices and isinstance(all_voices, (list, tuple)):
                # Try to filter voices that contain the language code
                filtered_voices = [voice for voice in all_voices if language in voice.lower()]
                if filtered_voices:
                    return filtered_voices
                # If no language-specific filtering worked, return all voices
                return list(all_voices)

            # Method 3: Check for voice_languages mapping
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
