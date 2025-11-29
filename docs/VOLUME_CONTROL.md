# Volume Control Feature

## Overview

The Voice Replay integration now includes automatic volume control functionality that temporarily increases the volume before playing TTS announcements or recorded audio, then restores the original volume after playback.

## Features

- **Configurable Volume Boost**: Users can configure the amount of volume increase (5% to 30% in 5% increments)
- **Smart Volume Management**: Automatically stores current volume, increases it, and restores it after playback
- **Device Compatibility**: Works with both Sonos speakers and regular media players
- **Intelligent Timing**: Different restore delays for Sonos vs. regular players to account for device-specific behavior

## Configuration Options

### Volume Boost Enabled

- **Type**: Boolean (On/Off)
- **Default**: Enabled (True)
- **Description**: Whether to enable volume boost functionality

### Volume Boost Amount

- **Type**: Number (Slider)
- **Range**: 0.05 - 0.30 (5% - 30%)
- **Default**: 0.1 (10%)
- **Step**: 0.05 (5%)
- **Description**: Amount to increase volume during announcements

## How It Works

### For TTS Announcements

1. System retrieves current volume level from the media player
2. If volume boost is enabled, volume is increased by the configured amount
3. TTS announcement is played
4. After TTS completes, original volume is restored automatically

### For Recorded Audio

1. Same process as TTS announcements
2. Audio duration is calculated when possible for optimal timing
3. Volume is restored after audio playback completes

### Sonos-Specific Handling

- Sonos speakers use slightly longer restoration delays (8 seconds vs 5 seconds)
- Volume restoration is integrated with Sonos snapshot/restore functionality
- Handles both the main Sonos restore and volume restore operations

### Error Handling

- If volume level cannot be retrieved, the feature gracefully disables for that session
- Restoration continues even if the boost operation fails
- Comprehensive logging for troubleshooting

## Technical Details

### Volume Limits

- Maximum volume is capped at 1.0 (100%) to prevent audio distortion
- If current volume + boost exceeds 1.0, it's limited to 1.0

### Timing

- **Regular Players**: 5-second delay before volume restoration
- **Sonos Players**: 8-second delay to account for Sonos-specific behavior
- **Dynamic Timing**: For recorded audio, uses actual audio duration when available

### Integration Points

- Configuration in `config_flow.py`
- Volume management in `ui.py`
- Settings storage in `__init__.py`
- Constants in `const.py`

## Usage

1. Install and configure the Voice Replay integration
2. In the integration options, enable "Volume Boost"
3. Adjust the "Volume Boost Amount" slider to desired level (10% recommended)
4. Test with TTS announcements or recorded audio
5. The system will automatically manage volume during playback

## Troubleshooting

### Volume Not Increasing

- Check that "Volume Boost Enabled" is turned on in integration options
- Verify the media player supports volume control
- Check Home Assistant logs for volume-related error messages

### Volume Not Restoring

- Check Home Assistant logs for restoration errors
- For Sonos: Ensure Sonos integration is working properly
- Volume restoration runs automatically in the background

### Configuration Not Saving

- Ensure you click "Submit" after changing volume settings
- Restart Home Assistant if changes don't take effect

## Logging

The integration provides detailed logging for volume operations:

- Volume boost operations
- Volume restoration
- Error conditions
- Timing information

Enable debug logging for `custom_components.voice-replay` to see detailed volume control information.
