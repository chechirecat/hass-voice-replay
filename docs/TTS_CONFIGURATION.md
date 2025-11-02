# TTS Configuration Guide

This guide explains how to configure Text-to-Speech (TTS) engines with the Voice Replay integration for optimal voice and speaker selection.

## Overview

The Voice Replay integration supports all Home Assistant TTS engines, with enhanced configuration options for modern TTS services like Piper, Google TTS, and other advanced speech synthesis engines. The integration automatically detects your TTS capabilities and provides appropriate configuration options.

## Key Features

### 1. Voice and Speaker Separation

For TTS engines that support multiple speakers per voice model, the configuration separates:

- **Voice**: The main voice model (e.g., `de_DE-eva-low`, `en_US-amy-medium`)  
- **Speaker**: Optional speaker variant for multi-speaker voices (e.g., `eva`, `p225`)

This ensures you get the exact voice and speaker combination you want.

### 2. Smart TTS Detection

The integration automatically detects your TTS engine capabilities:

- Recognizes modern TTS engines (Piper, Google TTS, etc.)
- Detects available voice and speaker options
- Handles both simple and advanced TTS configurations  
- Supports various language format variations (`de_DE`, `de-DE`, `de`)

### 3. Intelligent TTS Calls

When generating speech, the integration:

- Uses the optimal format for your specific TTS engine
- Separates voice and speaker parameters when supported
- Falls back to combined voice names for simpler engines
- Validates configurations before making TTS calls

### 4. Enhanced Setup Process

The configuration flow provides:

- Step-by-step voice and speaker selection
- Automatic detection of available options for your TTS engine
- Validation of voice-speaker combinations
- Clear error messages for invalid configurations
- Manual entry option when auto-detection isn't available

## Configuration Steps

### Step 1: Engine Selection
Choose your TTS engine. The integration will auto-detect Wyoming engines.

### Step 2: Language Selection  
Select the language for your chosen TTS engine. Wyoming engines will show language-specific options.

### Step 3: Voice Selection
Choose from available voices for your selected language. Wyoming engines will show properly enumerated voices.

### Step 4: Speaker Selection (if applicable)
For multi-speaker voices (common in Piper), select the specific speaker. This step only appears if the selected voice supports multiple speakers.

## Wyoming Protocol Specifics

### Voice Configuration Format

For Wyoming TTS entities, options are formatted as:
```python
{
    "voice": "voice_name",      # Main voice identifier
    "speaker": "speaker_name"   # Optional speaker identifier
}
```

### Compatibility Detection

The integration detects Wyoming TTS entities by checking:

1. Entity ID contains `wyoming`
2. `supported_options` attribute contains `speaker`
3. `integration` or `platform` attributes equal `wyoming`
4. Attribution mentions Wyoming or Piper

### Voice Enumeration

Wyoming TTS entities expose voices through:
- `supported_voices` attribute (structured by language)
- `async_get_supported_voices()` method
- Language-specific attributes like `voices_de_DE`

### Speaker Enumeration

Speaker detection checks for:
- Voice-specific speaker attributes (`speakers_{voice_name}`)
- General speakers attribute
- Speaker information embedded in voice names
- Voice-speaker mapping attributes

## Testing with Piper TTS

To test the Wyoming Protocol compatibility:

1. Install Piper TTS as a Wyoming integration in Home Assistant
2. Configure Voice Replay to use the Piper TTS entity
3. Verify that:
   - Languages are properly detected and listed
   - Voices are enumerated correctly for each language
   - Multi-speaker voices show speaker selection options
   - TTS calls work with both voice and speaker parameters

## Error Handling

The integration provides specific error messages for:
- Invalid voice selections
- Unavailable speaker options
- Engine compatibility issues
- Configuration validation failures

## Backward Compatibility

The improvements maintain backward compatibility with:
- Non-Wyoming TTS engines
- Existing voice configurations
- Legacy voice naming conventions
- Combined voice-speaker names

## Technical Implementation

### Key Files Modified

1. **config_flow.py**: Enhanced configuration flow with voice/speaker separation
2. **ui.py**: Updated TTS call logic for Wyoming Protocol compatibility  
3. **__init__.py**: Added speaker configuration storage
4. **strings.json**: Added localized error messages and descriptions

### New Methods Added

- `_get_voice_speakers()`: Enumerate available speakers for a voice
- `_validate_voice_speaker_combination()`: Validate voice-speaker pairs
- `_is_wyoming_engine()`: Detect Wyoming TTS entities
- `_is_wyoming_tts()`: Runtime Wyoming entity detection

This enhancement ensures that Voice Replay works seamlessly with both traditional TTS engines and modern Wyoming Protocol implementations like Piper TTS.