# Changelog

All notable changes to the Voice Replay Home Assistant Integration will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Enhanced frontend-backend integration with configurable countdown timing
- Improved microphone readiness detection using browser APIs
- Dynamic countdown duration based on backend `prepend_silence_seconds` configuration
- Recording starts immediately during countdown for zero audio loss

### Changed
- Frontend now fetches configuration from backend `/api/voice-replay/tts_config` endpoint
- TTS config endpoint now returns full configuration including `prepend_silence_seconds`
- Studio-style recording flow with better user feedback and state management

### Fixed
- Eliminated audio clicks at beginning of recordings through smart timing
- Perfect synchronization between frontend countdown and backend silence processing

## [0.8.1] - 2025-11-02

### Added
- Enhanced TTS configuration endpoint with full settings exposure
- Better frontend-backend configuration synchronization

### Changed
- Improved release workflow with comprehensive release notes

### Fixed
- Issue tracker URL in manifest.json (corrected typo)

## [0.8.0] - 2025-11-01

### Added
- Configurable silence prepending (0-10 seconds) to prevent audio cutoffs
- Studio-style recording countdown with microphone readiness detection
- Advanced microphone preparation using browser APIs
- Volume boost and restore functionality
- Comprehensive TTS engine support with voice and speaker selection

### Changed
- Unified recording flow with preparation, countdown, and recording phases
- Enhanced user experience with clear status messages and visual feedback

### Fixed
- Audio click/pop at beginning of recordings
- Microphone initialization timing issues
- Media source playback reliability for Sonos speakers

## [0.7.1] - 2025-10-30

### Added
- Initial release of Voice Replay integration
- Voice recording API with WebM to MP3 conversion
- Text-to-speech API with configurable engines
- Multi-room audio support for Home Assistant media players
- RESTful API endpoints for frontend integration
- Home Assistant authentication and security

### Features
- `/api/voice-replay/upload` - Audio recording and TTS requests
- `/api/voice-replay/media_players` - Available media player discovery
- `/api/voice-replay/tts_config` - TTS configuration management
- Support for various audio formats (WebM, MP3, WAV, M4A)
- FFmpeg integration for audio conversion
- Sonos-specific optimization and snapshot/restore functionality

---

## Release Types

- **Major** (x.0.0): Breaking changes, major new features
- **Minor** (0.x.0): New features, enhancements, non-breaking changes  
- **Patch** (0.0.x): Bug fixes, minor improvements

## Contributing

When contributing changes, please:
1. Add entries to the [Unreleased] section
2. Follow the format: `### Added/Changed/Fixed`
3. Include brief, user-focused descriptions
4. Reference issue numbers when applicable

## Links

- [Repository](https://github.com/chechirecat/hass-voice-replay)
- [Issues](https://github.com/chechirecat/hass-voice-replay/issues)
- [Voice Replay Card](https://github.com/chechirecat/hass-voice-replay-card)