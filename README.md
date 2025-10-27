# Voice Replay - Home Assistant Integration & Card

[![GitHub Release](https://img.shields.io/github/release/chechirecat/hass-voice-replay.svg?style=flat-square)](https://github.com/chechirecat/hass-voice-replay/releases)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square)](https://hacs.xyz/docs/faq/custom_repositories)
[![License](https://img.shields.io/github/license/chechirecat/hass-voice-replay.svg?style=flat-square)](LICENSE)
[![GitHub Activity](https://img.shields.io/github/commit-activity/y/chechirecat/hass-voice-replay.svg?style=flat-square)](https://github.com/chechirecat/hass-voice-replay/commits/main)

🎤 Record voice messages and generate text-to-speech to play on your Home Assistant media players!

## What's Included

This repository provides **two components**:

1. **🔌 Voice Replay Integration** - Backend services for recording and TTS
2. **🎨 Voice Replay Card** - Beautiful Lovelace dashboard card

## Features

🎤 **Voice Recording** - Record audio directly from your browser  
🗣️ **Text-to-Speech** - Generate speech using Home Assistant's TTS services  
📱 **Mobile Optimized** - Touch-friendly interface with large buttons  
🎨 **Theme Integration** - Automatically matches your Home Assistant theme  
🏠 **Multi-Room Audio** - Play on any media player in your home  
⚙️ **Configurable** - Customize appearance and default settings  

## Installation

### HACS (Recommended)

1. Make sure you have HACS installed: https://hacs.xyz
2. Add this repository as a custom repository to HACS:
   [![Add Repository](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=chechirecat&repository=hass-voice-replay&category=integration)
3. Install the integration via HACS
4. Restart Home Assistant
5. Set up the integration:  
   [![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=voice-replay)

**✨ HACS automatically handles the frontend component - no manual steps needed!**

### Manual Installation

#### Integration
1. Copy `custom_components/voice-replay` to your Home Assistant config directory
2. Restart Home Assistant
3. Add the integration: Settings → Devices & Services → Add Integration → "Voice Replay"

#### Card Resource (Manual Installation Only)
For manual installations, you need to add the card resource:
1. Copy `custom_components/voice-replay/voice-replay-card.js` to `<config>/www/voice-replay-card.js`
2. Go to Settings → Dashboards → Resources
3. Add resource:
   - URL: `/local/voice-replay-card.js`
   - Resource Type: JavaScript Module
   - Go to Settings → Dashboards → Resources  
   - Click "Add Resource"
   - URL: `/local/voice-replay-card.js`
   - Resource Type: JavaScript Module

## Using the Card

Add the card to your dashboard:

```yaml
type: custom:voice-replay-card
```

### Card Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `type` | string | **Required** | `custom:voice-replay-card` |
| `entity` | string | Optional | Default media player entity ID |
| `title` | string | "Voice Replay" | Card title |
| `show_title` | boolean | true | Show/hide the card title |

### Example Configurations

**Basic card:**
```yaml
type: custom:voice-replay-card
```

**Customized card:**
```yaml
type: custom:voice-replay-card
title: "Family Announcements"
entity: media_player.living_room_speaker
show_title: true
```

**Multiple cards for different rooms:**
```yaml
# Living Room Card
type: custom:voice-replay-card
title: "Living Room Audio"
entity: media_player.living_room_speaker

# Kitchen Card  
type: custom:voice-replay-card
title: "Kitchen Announcements"
entity: media_player.kitchen_speaker
```

## How It Works

1. **Recording**: Uses your browser's microphone to record audio
2. **Upload**: Sends audio to Home Assistant backend  
3. **Processing**: Integration creates a temporary URL for the audio
4. **Playback**: Calls `media_player.play_media` service on selected device
5. **TTS**: Uses Home Assistant's built-in TTS services directly
6. **Card Serving**: The integration automatically serves the card JavaScript at `/api/voice-replay/voice-replay-card.js`

## Browser Requirements

- **HTTPS Required**: Microphone access requires a secure connection
- **Supported Browsers**: Chrome, Firefox, Safari, Edge (modern versions)
- **Permissions**: Browser will request microphone permission on first use

## Troubleshooting

### Card Issues
- **Card not showing**: Verify the resource is properly added to Resources with URL `/api/voice-replay/voice-replay-card.js`
- **"No media players found"**: Check that you have media_player entities in HA
- **Recording fails**: Check HTTPS connection and browser permissions
- **Resource not found**: Make sure the Voice Replay integration is installed and running

### Integration Issues

- **Upload fails**: Check Home Assistant logs for detailed error messages
- **Audio doesn't play**: Verify media player supports the audio format
- **TTS not working**: Ensure TTS is configured in Home Assistant

### Getting Help

1. Check Home Assistant logs: Settings → System → Logs
2. Check browser console for JavaScript errors
3. Verify media players are working with other audio
4. Create an issue on GitHub with logs and setup details

## Advanced Usage

### Service Calls

The integration also provides a service for automation use:

```yaml
service: voice_replay.replay  
data:
  url: "https://example.com/audio.mp3"
  entity_id: media_player.living_room
```

### Integration with Automations

```yaml
- alias: "Doorbell Announcement"
  trigger:
    - platform: state
      entity_id: binary_sensor.doorbell
      to: "on"
  action:
    - service: tts.speak
      data:
        entity_id: media_player.whole_house
        message: "Someone is at the door"
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes  
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/chechirecat/hass-voice-replay/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/chechirecat/hass-voice-replay/discussions)
- 📖 **Documentation**: Check the README and code comments

## Credits

- Template used: [hass-integration-template](https://github.com/siku2/hass-integration-template)
- Inspired by similar voice integrations in the Home Assistant community
