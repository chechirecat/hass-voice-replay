# Voice Replay - Home Assistant Integration

[![GitHub Release](https://img.shields.io/github/release/chechirecat/hass-voice-replay.svg?style=flat-square)](https://github.com/chechirecat/hass-voice-replay/releases)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square)](https://hacs.xyz/docs/faq/custom_repositories)
[![License](https://img.shields.io/github/license/chechirecat/hass-voice-replay.svg?style=flat-square)](LICENSE)
[![GitHub Activity](https://img.shields.io/github/commit-activity/y/chechirecat/hass-voice-replay.svg?style=flat-square)](https://github.com/chechirecat/hass-voice-replay/commits/main)

🎤 Record voice messages and generate text-to-speech to play on your Home Assistant media players!

## What's This Repository

This repository provides the **🔌 Voice Replay Integration** - the backend services for voice recording and TTS functionality.

**🎨 Looking for the Lovelace Card?** The frontend card is in a separate repository:
👉 **[Voice Replay Card Repository](https://github.com/chechirecat/voice-replay-card)** 👈

## Features

🎤 **Voice Recording API** - Record audio via browser and save to media players  
🗣️ **Text-to-Speech API** - Generate speech using Home Assistant's TTS services  
🏠 **Multi-Room Audio** - Play on any media player in your home  
⚙️ **RESTful API** - Easy integration with custom cards and automations  
🔐 **Secure** - Built-in Home Assistant authentication

## Complete Setup (Integration + Card)

To get the full Voice Replay experience, you need both:

1. **This Integration** (backend services)
2. **[Voice Replay Card](https://github.com/chechirecat/voice-replay-card)** (frontend UI)  

## Installation

### HACS (Recommended)

1. Make sure you have HACS installed: https://hacs.xyz
2. Add this repository as a custom repository to HACS:
   [![Add Repository](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=chechirecat&repository=hass-voice-replay&category=integration)
3. Install the integration via HACS
4. Restart Home Assistant
5. Set up the integration:  
   [![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=voice-replay)

### Manual Installation

1. Copy `custom_components/voice-replay` to your Home Assistant config directory
2. Restart Home Assistant
3. Add the integration: Settings → Devices & Services → Add Integration → "Voice Replay"

## Frontend Card

**The Lovelace card is in a separate repository for easier management:**

🎨 **[Install Voice Replay Card](https://github.com/chechirecat/voice-replay-card)**

The card provides a beautiful touch-friendly interface for:
- 🎤 Recording voice messages
- 🗣️ Text-to-speech generation  
- 📱 Mobile-optimized controls
- 🎨 Theme integration

## API Endpoints

This integration provides RESTful API endpoints that can be used by the frontend card or other automations:

- **POST** `/api/voice-replay/upload` - Upload audio or TTS text for playback
- **GET** `/api/voice-replay/media_players` - List available media players  
- **GET** `/api/voice-replay/tts_config` - Check TTS configuration
- **GET** `/api/voice-replay/media/{filename}` - Serve temporary audio files

## Usage Examples

### Using with Automations

You can trigger voice playback from automations using the `voice_replay.replay` service:

```yaml
service: voice_replay.replay
data:
  entity_id: media_player.living_room
  message: "Hello from Home Assistant!"
  type: tts
```

### Using the REST API

```bash
# Upload a voice recording
curl -X POST http://homeassistant.local:8123/api/voice-replay/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "audio=@recording.webm" \
  -F "entity_id=media_player.living_room" \
  -F "type=recording"

# Generate TTS
curl -X POST http://homeassistant.local:8123/api/voice-replay/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "text=Hello World" \
  -F "entity_id=media_player.kitchen" \
  -F "type=tts"
```
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

1. **Recording**: Frontend card uses browser's microphone to record audio
2. **Upload**: Audio is sent to Home Assistant backend via REST API  
3. **Processing**: Integration creates a temporary URL for the audio
4. **Playback**: Calls `media_player.play_media` service on selected device
5. **TTS**: Uses Home Assistant's built-in TTS services directly

## Browser Requirements

- **HTTPS Required**: Microphone access requires a secure connection
- **Supported Browsers**: Chrome, Firefox, Safari, Edge (modern versions)
- **Permissions**: Browser will request microphone permission on first use

## Troubleshooting

### Integration Issues

- **Upload fails**: Check Home Assistant logs for detailed error messages
- **Audio doesn't play**: Verify media player supports the audio format
- **TTS not working**: Ensure TTS is configured in Home Assistant
- **"No media players found"**: Check that you have media_player entities in HA

### API Issues

- **401 Unauthorized**: Ensure you're using a valid Home Assistant access token
- **404 Not Found**: Verify the Voice Replay integration is installed and running
- **500 Server Error**: Check Home Assistant logs for backend errors

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
