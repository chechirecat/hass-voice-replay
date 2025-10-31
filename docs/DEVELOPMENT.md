# Development Guide

This guide covers development setup, architecture, and contribution guidelines for the Voice Replay Integration.

## Table of Contents

- [Development Environment](#development-environment)
- [Project Structure](#project-structure)
- [API Architecture](#api-architecture)
- [Testing](#testing)
- [Release Process](#release-process)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)

## Development Environment

### Prerequisites

- **Home Assistant** development environment
- **Python 3.11+** (latest supported by HA)
- **Git** for version control
- **Text editor/IDE** (VS Code recommended with Python extensions)

### Quick Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/chechirecat/hass-voice-replay.git
   cd hass-voice-replay
   ```

2. **Install development dependencies:**
   ```bash
   pip install -r requirements_dev.txt
   ```

3. **Set up pre-commit hooks:**
   ```bash
   pre-commit install
   ```

4. **Copy to Home Assistant:**
   ```bash
   # Copy the integration to your HA config
   cp -r custom_components/voice-replay /path/to/homeassistant/config/custom_components/
   ```

5. **Restart Home Assistant** and add the integration

### Development Tools

The project includes several development tools:

- **Linting:** `ruff` for code quality
- **Formatting:** `ruff` for code formatting  
- **Type checking:** `mypy` for static analysis
- **Testing:** `pytest` for unit tests
- **Pre-commit:** Automated code quality checks

### Running Development Tools

```bash
# Run all linting checks
./scripts/lint.sh

# Format code
ruff format custom_components/

# Type checking
mypy custom_components/voice-replay/

# Run tests
pytest tests/
```

## Project Structure

```
custom_components/voice-replay/
├── __init__.py              # Integration entry point
├── config_flow.py           # Configuration UI
├── const.py                 # Constants and configuration
├── manifest.json            # Integration metadata
├── services.py              # Service implementations
├── services.yaml            # Service definitions
├── ui.py                    # Web UI and API endpoints
└── translations/
    ├── de.json              # german translation
    └── en.json              # English translations

scripts/
├── develop.sh               # Development setup script
├── lint.sh                  # Linting script
├── setup.sh                 # Project setup script
└── release.sh               # Release automation script

tests/
├── conftest.py              # Test configuration
├── test_config_flow.py      # Config flow tests
├── test_init.py             # Integration tests
└── test_services.py         # Service tests
```

### Key Files Explained

#### `__init__.py`
The integration entry point that handles:
- Integration setup and unloading
- Service registration
- Platform initialization

#### `config_flow.py`  
Configuration flow for the integration UI:
- User setup wizard
- Options configuration
- Validation logic

#### `ui.py`
Web API endpoints and UI components:
- RESTful API for audio upload
- Media serving endpoints  
- Frontend integration points

#### `services.py`
Core business logic:
- Audio processing
- TTS integration
- Media player interaction

## API Architecture

### RESTful API Endpoints

The integration exposes several REST API endpoints:

#### Audio Upload
```http
POST /api/voice-replay/upload
Content-Type: multipart/form-data

Parameters:
- audio: Audio file (for recordings)
- text: Text content (for TTS)
- entity_id: Target media player
- type: "recording" | "tts"
```

#### Media Players
```http
GET /api/voice-replay/media_players
Authorization: Bearer <token>

Returns: List of available media players
```

#### TTS Configuration
```http
GET /api/voice-replay/tts_config
Authorization: Bearer <token>

Returns: TTS service configuration
```

#### Media Serving
```http
GET /api/voice-replay/media/{filename}
Authorization: Bearer <token>

Returns: Temporary audio file
```

### Service Architecture

#### Voice Replay Service
```yaml
service: voice_replay.replay
data:
  entity_id: media_player.living_room
  message: "Hello World"
  type: tts  # or "recording"
  url: "https://example.com/audio.mp3"  # optional
```

### Integration with Home Assistant

#### Media Player Integration
The integration leverages HA's media player platform:
- Automatic media player discovery
- Format compatibility checking
- Volume and state management

#### TTS Integration  
Seamless integration with HA's TTS services:
- Uses configured TTS platform
- Respects TTS service settings
- Handles multiple TTS engines

#### Authentication
Built-in Home Assistant authentication:
- Bearer token validation
- User permission checking
- Secure API access

## Testing

### Unit Tests

Run the test suite:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=custom_components.voice_replay

# Run specific test file
pytest tests/test_services.py

# Run with verbose output
pytest -v
```

### Integration Tests

Test the integration in a live Home Assistant environment:

1. **Install in development HA instance**
2. **Configure the integration**  
3. **Test API endpoints manually**
4. **Verify service calls work**
5. **Test with different media players**

### Manual Testing Checklist

#### Basic Functionality
- [ ] Integration installs without errors
- [ ] Configuration flow completes successfully
- [ ] API endpoints respond correctly
- [ ] Service calls execute properly
- [ ] Audio upload and playback works

#### Error Handling
- [ ] Invalid audio formats rejected gracefully
- [ ] Network errors handled properly
- [ ] Media player errors reported correctly
- [ ] Authentication failures handled
- [ ] TTS service errors managed

#### Performance
- [ ] Large audio files handled efficiently
- [ ] Multiple concurrent requests work
- [ ] Memory usage remains reasonable
- [ ] Temporary files cleaned up properly

### Testing with Different Configurations

Test various Home Assistant setups:

```yaml
# Different TTS services
tts:
  - platform: google_translate
  - platform: amazon_polly
  - platform: piper

# Different media players  
media_player:
  - platform: sonos
  - platform: cast
  - platform: mpd
```

## Release Process

### Automated Release

The repository includes automated release scripts. See **[Release Automation Guide](RELEASE_AUTOMATION.md)** for complete details.

### Version Management

The integration version is managed in three files:
- `manifest.json` - Integration version
- `pyproject.toml` - Python package version
- `tests/test.js` - Test file version

### Release Checklist

Before releasing:

1. **Test thoroughly** in development environment
2. **Update documentation** as needed
3. **Check version consistency** across all files
4. **Verify CI/CD pipeline** passes
5. **Run release script** with appropriate increment

```bash
# Patch release (bug fixes)
./scripts/release.sh

# Minor release (new features)  
./scripts/release.sh --increment minor

# Major release (breaking changes)
./scripts/release.sh --increment major
```

## Contributing

### Code Style

The project follows these coding standards:

- **PEP 8** compliance (enforced by ruff)
- **Type hints** for all functions
- **Docstrings** for all public methods
- **Error handling** for all I/O operations
- **Logging** for debugging and monitoring

### Example Code Patterns

```python
# Good: Type hints and error handling
async def upload_audio(
    hass: HomeAssistant,
    audio_data: bytes,
    entity_id: str,
    audio_format: str = "webm"
) -> dict[str, Any]:
    """Upload audio data and prepare for playback.
    
    Args:
        hass: Home Assistant instance
        audio_data: Raw audio bytes
        entity_id: Target media player entity ID
        audio_format: Audio format (webm, mp3, etc.)
        
    Returns:
        Dictionary with upload result and media URL
        
    Raises:
        ValueError: If audio data is invalid
        HomeAssistantError: If media player not found
    """
    try:
        # Validate inputs
        if not audio_data:
            raise ValueError("Audio data cannot be empty")
            
        if not entity_id.startswith("media_player."):
            raise ValueError(f"Invalid media player entity: {entity_id}")
        
        # Process audio
        filename = await _save_audio_file(hass, audio_data, audio_format)
        media_url = _create_media_url(hass, filename)
        
        _LOGGER.info("Audio uploaded successfully: %s", filename)
        
        return {
            "success": True,
            "filename": filename,
            "media_url": media_url
        }
        
    except Exception as err:
        _LOGGER.error("Failed to upload audio: %s", err)
        raise HomeAssistantError(f"Audio upload failed: {err}") from err
```

### Commit Message Format

Use conventional commit format:

```bash
# Feature additions
git commit -m "feat: add support for custom TTS voices"

# Bug fixes  
git commit -m "fix: handle media player unavailable state"

# Documentation
git commit -m "docs: update API endpoint documentation"

# Code refactoring
git commit -m "refactor: simplify audio processing logic"

# Tests
git commit -m "test: add integration tests for TTS service"
```

### Pull Request Process

1. **Fork the repository**
2. **Create feature branch:** `git checkout -b feature/description`
3. **Make changes** with proper testing
4. **Run linting and tests:** `./scripts/lint.sh && pytest`
5. **Update documentation** if needed
6. **Submit pull request** with clear description

#### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature  
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings introduced
```

## Troubleshooting

### Development Issues

#### Import Errors
```python
# Common issue: Module not found
ModuleNotFoundError: No module named 'custom_components.voice_replay'

# Solution: Ensure proper PYTHONPATH or install in development mode
pip install -e .
```

#### Integration Not Loading
```yaml
# Check Home Assistant logs for:
Logger: homeassistant.loader
Source: loader.py:XXX
Integration voice_replay not found.

# Solution: Verify custom_components directory structure
```

#### API Endpoints Not Working
```bash
# Check if integration is loaded
curl http://homeassistant.local:8123/api/voice-replay/media_players

# Common issue: 404 Not Found
# Solution: Restart HA and verify integration is active
```

### Code Quality Issues

#### Linting Failures
```bash
# Run linter to see specific issues
ruff check custom_components/

# Auto-fix many issues
ruff check --fix custom_components/
```

#### Type Check Failures
```bash
# Run mypy for detailed type errors
mypy custom_components/voice-replay/

# Common issue: Missing type hints
# Solution: Add proper type annotations
```

### Performance Issues

#### Memory Leaks
Monitor memory usage with large audio files:
```python
import tracemalloc

tracemalloc.start()
# ... your code ...
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
```

#### Slow API Responses
Profile API endpoint performance:
```python
import time
start = time.time()
# ... API call ...
print(f"API call took {time.time() - start:.2f} seconds")
```

### Getting Help

1. **Check Home Assistant logs** for detailed error messages
2. **Review integration documentation** in the code
3. **Search existing GitHub issues** for similar problems
4. **Create detailed issue** with logs and reproduction steps
5. **Join Home Assistant Discord** for community support

## Advanced Development

### Custom Audio Processing

Extend audio processing capabilities:
```python
async def process_audio_custom(
    audio_data: bytes,
    format_in: str,
    format_out: str
) -> bytes:
    """Custom audio processing pipeline."""
    # Add noise reduction, normalization, etc.
    pass
```

### Alternative TTS Integration

Integrate with external TTS services:
```python
async def generate_tts_external(
    text: str,
    voice: str,
    service: str
) -> bytes:
    """Generate TTS using external service."""
    # Integration with cloud TTS APIs
    pass
```

### Media Player Extensions

Add support for specific media player features:
```python
async def enhanced_media_play(
    hass: HomeAssistant,
    entity_id: str,
    media_url: str,
    **kwargs
) -> None:
    """Enhanced media playback with specific features."""
    # Add fade-in, queue management, etc.
    pass
```

---

This guide provides comprehensive coverage of development practices for the Voice Replay Integration. Keep it updated as the project evolves! 🚀