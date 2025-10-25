# Voice Replay (Home Assistant custom component)

This integration lets you request a voice recording from a Companion/mobile browser and play it on a media_player (Sonos or other), pausing and resuming the current playback.

## How it works

- Call the service `voice_replay.request_recording` with the Companion device id (the suffix used in notify service: `notify.mobile_app_<device_id>`) and target `entity_id` (a `media_player.*`).
- The integration generates a one-time token and sends a notification with a link to a small recording web page.
- The mobile user taps the link, records a short clip, and uploads it. Home Assistant saves the file under `/config/www/voice_replay/`.
- The integration pauses the given media_player, plays the uploaded clip via a direct URL, and after the clip duration, attempts to resume the previous playback.

## Notes

- If Sonos can't play the raw upload, install ffmpeg on the host (or the ffmpeg add-on) — the integration will transcode to MP3 if ffmpeg is available.
- Add cleanup for /www/voice_replay if you expect many files (not included).
