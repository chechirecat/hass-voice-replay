# hass-voice-replay

Home Assistant custom integration to request short voice recordings from the Companion app (or browser) and play them on networked media players (Sonos, etc.), pausing/resuming playback.

Repository contents:
- custom_components/voice_replay/manifest.json
- custom_components/voice_replay/__init__.py
- custom_components/voice_replay/README.md

Quick install (manual):
1. Create a GitHub repository named `hass-voice-replay` (or create a directory locally).
2. In your Home Assistant configuration directory, place the `custom_components/voice_replay` folder (with files) under `/config/custom_components/`.
3. Restart Home Assistant.
4. Use the service `voice_replay.request_recording`:

Example:
```yaml
service: voice_replay.request_recording
data:
  device_id: my_android_phone
  entity_id: media_player.living_room_sonos
  message: "Tap to record a quick message for the living room speaker"
```
