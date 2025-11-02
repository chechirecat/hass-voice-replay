# Release Notes Template

This template helps create consistent, comprehensive release notes for the Voice Replay Integration.

# Release Notes Template

This template helps create consistent, comprehensive release notes for the Voice Replay Integration.

## Automatic Version Comparison

The release workflow now automatically generates comparison URLs between releases:

- **Current release vs Latest**: Automatically detects the GitHub "Latest" release and creates a comparison URL
- **Stable baseline**: Compares against the release marked as "Latest" (not just the previous chronological tag)
- **First release**: Falls back to showing commit history if no latest release exists
- **Example**: For v0.8.2 compared against v0.7.0 (Latest) → `https://github.com/chechirecat/hass-voice-replay/compare/v0.7.0...v0.8.2`

### How It Works
1. Uses GitHub API to fetch the release marked as "Latest"
2. Creates comparison URL from Latest → Current release
3. This ensures comparison against stable baseline, not just previous development tags

This eliminates the need to manually update comparison URLs in release notes and provides meaningful comparisons against stable releases.

## Basic Release Notes Structure

```markdown
## 🎤 Voice Replay Integration v{VERSION}

### Installation

#### Via HACS (Recommended)
[![Add Repository](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=chechirecat&repository=hass-voice-replay&category=integration)

1. Click the badge above to add this repository to HACS
2. Search for "Voice Replay" in HACS Integrations
3. Install and restart Home Assistant
4. Go to Settings → Devices & Services → Add Integration → "Voice Replay"

#### Manual Installation
1. Download `voice-replay.zip` from this release
2. Extract to your `<config>/custom_components/` folder
3. Restart Home Assistant
4. Add the integration via Settings → Devices & Services

### Requirements
* Home Assistant 2025.10.4 or newer
* Voice Replay Card (install separately for frontend UI)

### What's New in v{VERSION}

### Features Overview
* 🎤 **Voice Recording API** - Record audio via browser and save to media players
* 🗣️ **Text-to-Speech API** - Generate speech using Home Assistant's TTS services
* 🏠 **Multi-Room Audio** - Play on any media player in your home
* ⚙️ **Configurable Settings** - Silence prepend, volume boost, and more
* 🔐 **Secure** - Built-in Home Assistant authentication
* 📱 **RESTful API** - Easy integration with custom cards and automations

### Frontend Card
**🎨 Looking for the Lovelace Card?** Install the companion frontend card:
👉 **[Voice Replay Card Repository](https://github.com/chechirecat/hass-voice-replay-card)** 👈

### Need Help?
* 📚 [Documentation](https://github.com/chechirecat/hass-voice-replay/blob/main/README.md)
* 🐛 [Report Issues](https://github.com/chechirecat/hass-voice-replay/issues)
* 💬 [Discussions](https://github.com/chechirecat/hass-voice-replay/discussions)

{CHANGELOG_CONTENT}

```

## Release Types

### Major Release (x.0.0)
- Breaking changes
- Major new features
- Significant architecture changes
- May require user action to upgrade

### Minor Release (0.x.0)
- New features
- Enhancements
- Non-breaking changes
- Backward compatible

### Patch Release (0.0.x)
- Bug fixes
- Security fixes
- Minor improvements
- Documentation updates

## Changelog Categories

### Added
- New features
- New API endpoints
- New configuration options
- New integrations or compatibility

### Changed
- Improvements to existing features
- Performance enhancements
- UI/UX improvements
- Dependency updates

### Fixed
- Bug fixes
- Security fixes
- Error handling improvements
- Compatibility fixes

### Deprecated
- Features that will be removed
- API endpoints being phased out
- Configuration options being replaced

### Removed
- Features that have been removed
- Deprecated items that are no longer supported
- Breaking changes

### Security
- Security-related fixes
- Vulnerability patches
- Authentication improvements

## Release Checklist

Before releasing:

- [ ] Update version in `manifest.json`
- [ ] Update version in `pyproject.toml`
- [ ] Update version in `test.js`
- [ ] Update CHANGELOG.md with new version
- [ ] Run `.\scripts\release.ps1` to validate and create release
- [ ] Verify GitHub Actions workflow completes successfully
- [ ] Test installation via HACS
- [ ] Update documentation if needed

## Examples

### Feature Release
```markdown
### Added
- New voice recording timeout configuration
- Support for additional audio formats (FLAC, OGG)
- Integration with HomeKit speakers

### Changed
- Improved error handling for network timeouts
- Enhanced audio quality with better compression settings
- Updated dependency to Home Assistant 2025.11.0+

### Fixed
- Fixed issue with Sonos speakers not resuming after announcements
- Resolved audio crackling on certain devices
- Fixed configuration validation for custom TTS engines
```

### Bug Fix Release
```markdown
### Fixed
- Critical fix for audio recording failures on Firefox
- Resolved memory leak in long recording sessions
- Fixed configuration migration from version 0.7.x
- Corrected timezone handling in scheduled announcements
```