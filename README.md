# hass-voice-replay

Voice Replay - Home Assistant custom integration skeleton.

Installation:
1. Copy the custom_components/voice_replay folder into your Home Assistant config directory.
2. Restart Home Assistant.
3. Call the service voice_replay.replay with optional url or media_content.

Repository adapted to the hass-integration-template structure with CI and tests.

Repository contents:

- custom_components/voice_replay/manifest.json
- custom_components/voice_replay/__init__.py
- custom_components/voice_replay/README.md

Quick install (manual):

1. Create a GitHub repository named `hass-voice-replay` (or create a directory locally).
1. In your Home Assistant configuration directory, place the `custom_components/voice_replay` folder (with files) under `/config/custom_components/`.
1. Restart Home Assistant.
1. Use the service `voice_replay.request_recording`:

Example:

```yaml
service: voice_replay.request_recording
data:
  device_id: my_android_phone
  entity_id: media_player.living_room_sonos
  message: "Tap to record a quick message for the living room speaker"
```
