# Voice Replay Custom Component

A Home Assistant custom component that provides a native voice recording and playback interface.

## Features

- **Native Integration**: No external URLs or iframes - runs directly within Home Assistant's authenticated environment
- **Voice Recording**: Record audio directly from your browser or Home Assistant app
- **Media Player Integration**: Play recordings on any Home Assistant media player
- **Sidebar Panel**: Accessible from the Home Assistant sidebar
- **Secure**: Uses Home Assistant's built-in authentication and API

## Installation

1. Copy the `voice-replay` folder to your `custom_components` directory
2. Restart Home Assistant
3. Go to Configuration > Integrations
4. Click "Add Integration" and search for "Voice Replay"
5. Complete the setup (no configuration required)

## Usage

1. After installation, you'll see "Voice Replay" in your Home Assistant sidebar
2. Click on it to open the voice recording interface
3. Select a media player from the dropdown
4. Click the microphone button to start recording
5. Click again to stop recording
6. Click "Play Recording" to play it on your selected media player

## API Endpoints

The component provides several API endpoints:

- `/api/voice-replay/panel` - Main UI interface
- `/api/voice-replay/media_players` - List available media players
- `/api/voice-replay/upload` - Handle audio upload and playback
- `/api/voice-replay/media/{filename}` - Serve temporary audio files

## Technical Details

This component creates a native Home Assistant panel that:
- Uses the browser's MediaRecorder API for audio recording
- Uploads recordings to Home Assistant's backend
- Integrates with Home Assistant's media player services
- Provides a clean, responsive UI that matches Home Assistant's design

No external authentication is required since it runs within Home Assistant's authenticated environment.

## Migration from External UI

This version replaces the previous external URL-based approach with a native Home Assistant integration, eliminating authentication issues and providing a better user experience.
