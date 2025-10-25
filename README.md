# Voice Replay Home Assistant Integration

[![GitHub Release](https://img.shields.io/github/release/chechirecat/hass-voice-replay.svg?style=flat-square)](https://github.com/chechirecat/hass-voice-replay/releases)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square)](https://hacs.xyz/docs/faq/custom_repositories)

[![License](https://img.shields.io/github/license/chechirecat/hass-voice-replay.svg?style=flat-square)](LICENSE)
[![GitHub Activity](https://img.shields.io/github/commit-activity/y/chechirecat/hass-voice-replay.svg?style=flat-square)](https://github.com/chechirecat/hass-voice-replay/commits/main)

A small Home Assistant custom integration to replay the captured voice clips on a media player.

## Installation

### HACS (recommended)

1. Make sure you have HACS installed: https://hacs.xyz
1. Add this repository as a custom repository to HACS:
   [![Add Repository](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=chechirecat&repository=hass-voice-replay&category=integration)
1. Install the integration via HACS.
1. Restart Home Assistant.
1. Set up the integration using the UI:  
   [![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=voice-replay)

### Manual (local Home Assistant)

1. Copy the folder custom_components/voice-replay into your Home Assistant config directory:
   <config_dir>/custom_components/voice-replay
1. Restart Home Assistant.
1. Add the integration: Settings → Devices & Services → Add Integration → "Voice Replay".

## Usage

- During setup you can provide a UI URL (default suggested). The integration exposes a redirect endpoint:
  /api/voice-replay/ui — opens the configured UI URL.
- Service: voice-replay.replay
  - Example service call data:
    {"url": "https://example.com/test.mp3"}
  - The integration stores the last service payload at hass.data["voice-replay"]["voice-replay_data"]["last_replay"] for debugging.

If you want a sidebar entry, add this to your configuration.yaml (panel_iframe) pointing to the local redirect endpoint:

```
panel_iframe:
  voice-replay:
    title: Voice Replay
    icon: mdi:microphone
    url: "http://<home_assistant_host>:8123/api/voice-replay/ui"
```

## Contributing

Contributions are welcome. Please open issues or PRs on GitHub and follow standard contribution workflows. See CONTRIBUTING.md if present.

## Links

- Template used: hass-integration-template — https://github.com/siku2/hass-integration-template  
- Home Assistant developer docs: https://developers.home-assistant.io/docs/creating_integration_file_structure
- HACS docs: https://hacs.xyz
