"""Native UI implementation for Voice Replay with direct Home Assistant integration."""

from __future__ import annotations

import logging

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# API endpoints
PANEL_URL = f"/api/{DOMAIN}/panel"
PANEL_NAME = f"api:{DOMAIN}:panel"
UPLOAD_URL = f"/api/{DOMAIN}/upload"
UPLOAD_NAME = f"api:{DOMAIN}:upload"
MEDIA_PLAYERS_URL = f"/api/{DOMAIN}/media_players"
MEDIA_PLAYERS_NAME = f"api:{DOMAIN}:media_players"
MEDIA_URL = f"/api/{DOMAIN}/media"
MEDIA_NAME = f"api:{DOMAIN}:media"
TTS_CONFIG_URL = f"/api/{DOMAIN}/tts_config"
TTS_CONFIG_NAME = f"api:{DOMAIN}:tts_config"


class VoiceReplayPanelView(HomeAssistantView):
    """Serve the native Voice Replay panel HTML."""

    url = PANEL_URL
    name = PANEL_NAME
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        """Serve the Voice Replay panel."""
        _LOGGER.info("Voice Replay panel requested from %s", request.remote)

        html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Voice Replay</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {
            box-sizing: border-box;
        }
        html, body {
            margin: 0;
            padding: 0;
            height: 100%;
            font-family: var(--paper-font-body1_-_font-family), -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--primary-background-color, #fafafa);
            color: var(--primary-text-color, #212121);
            line-height: 1.5;
        }
        body {
            padding: 20px;
            overflow: auto;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            height: 100%;
        }
        .card {
            background: var(--card-background-color, white);
            border-radius: var(--ha-card-border-radius, 8px);
            padding: 20px;
            box-shadow: var(--ha-card-box-shadow, 0 2px 8px rgba(0,0,0,0.1));
            margin-bottom: 20px;
            border: var(--ha-card-border-width, 1px) solid var(--divider-color, #e0e0e0);
        }
        .mode-selector {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            justify-content: center;
        }
        .mode-option {
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            padding: 10px;
            border-radius: 8px;
            transition: background-color 0.3s;
        }
        .mode-option:hover {
            background-color: rgba(33, 150, 243, 0.1);
        }
        .mode-option input[type="radio"] {
            margin: 0;
        }
        .section {
            margin: 20px 0;
            padding: 15px;
            border-radius: 8px;
            background: rgba(0,0,0,0.02);
        }
        .section.hidden {
            display: none;
        }
        .record-button {
            background: #ff5722;
            color: white;
            border: none;
            border-radius: 50%;
            width: 80px;
            height: 80px;
            font-size: 24px;
            cursor: pointer;
            margin: 20px auto;
            display: block;
            transition: all 0.3s ease;
        }
        .record-button:hover { transform: scale(1.05); }
        .record-button.recording {
            background: #f44336;
            animation: pulse 1s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
        select, button, input[type="text"], textarea {
            padding: 10px;
            margin: 5px;
            border: 1px solid var(--divider-color, #ddd);
            border-radius: var(--ha-card-border-radius, 4px);
            font-size: 16px;
            font-family: inherit;
            background: var(--card-background-color, white);
            color: var(--primary-text-color, #212121);
        }
        textarea {
            width: calc(100% - 22px);
            min-height: 80px;
            resize: vertical;
        }
        button {
            background: var(--primary-color, #2196f3);
            color: var(--text-primary-color, white);
            cursor: pointer;
            transition: background-color 0.3s;
        }
        button:hover:not(:disabled) {
            background: var(--dark-primary-color, #1976d2);
        }
        button:disabled {
            background: var(--disabled-text-color, #ccc);
            cursor: not-allowed;
        }
        .tts-button {
            background: var(--light-primary-color, #4caf50);
        }
        .tts-button:hover:not(:disabled) {
            background: #388e3c;
        }
        .status {
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            text-align: center;
        }
        .status.success { background: #c8e6c9; color: #2e7d32; }
        .status.error { background: #ffcdd2; color: #c62828; }
        .status.info { background: #bbdefb; color: #1565c0; }
        .control-group {
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2>🎤 Voice Replay</h2>
            <p>Record audio or generate speech and play it on your selected media player</p>

            <div>
                <label for="mediaPlayer">Select Media Player:</label>
                <select id="mediaPlayer">
                    <option value="">Loading media players...</option>
                </select>
            </div>

            <div class="mode-selector">
                <label class="mode-option">
                    <input type="radio" name="mode" value="record" checked>
                    <span>🎤 Record Voice</span>
                </label>
                <label class="mode-option">
                    <input type="radio" name="mode" value="tts">
                    <span>🗣️ Text-to-Speech</span>
                </label>
            </div>

            <div id="recordSection" class="section">
                <h3>Voice Recording</h3>
                <button id="recordButton" class="record-button">🎤</button>
                <div class="control-group">
                    <button id="playRecordingButton" disabled>▶️ Play Recording</button>
                    <button id="stopButton" disabled>⏹️ Stop</button>
                </div>
                <audio id="audioPlayback" controls style="width: 100%; margin-top: 10px; display: none;"></audio>
            </div>

            <div id="ttsSection" class="section hidden">
                <h3>Text-to-Speech</h3>
                <textarea id="ttsText" placeholder="Enter the text you want to convert to speech..."></textarea>
                <div class="control-group">
                    <button id="generateSpeechButton" class="tts-button">🗣️ Generate & Play Speech</button>
                </div>
            </div>

            <div id="status" class="status" style="display: none;"></div>
        </div>
    </div>

    <script>
        let mediaRecorder;
        let recordedChunks = [];
        let isRecording = false;

        const recordButton = document.getElementById('recordButton');
        const playRecordingButton = document.getElementById('playRecordingButton');
        const stopButton = document.getElementById('stopButton');
        const mediaPlayerSelect = document.getElementById('mediaPlayer');
        const statusDiv = document.getElementById('status');
        const audioPlayback = document.getElementById('audioPlayback');
        const ttsText = document.getElementById('ttsText');
        const generateSpeechButton = document.getElementById('generateSpeechButton');
        const recordSection = document.getElementById('recordSection');
        const ttsSection = document.getElementById('ttsSection');
        const modeRadios = document.querySelectorAll('input[name="mode"]');

        // Load media players and TTS config on page load
        loadMediaPlayers();
        checkTTSAvailability();

        // Mode switching
        modeRadios.forEach(radio => {
            radio.addEventListener('change', switchMode);
        });

        function switchMode() {
            const selectedMode = document.querySelector('input[name="mode"]:checked').value;
            if (selectedMode === 'record') {
                recordSection.classList.remove('hidden');
                ttsSection.classList.add('hidden');
            } else {
                recordSection.classList.add('hidden');
                ttsSection.classList.remove('hidden');
            }
        }

        async function loadMediaPlayers() {
            try {
                const response = await fetch('/api/voice-replay/media_players');
                const players = await response.json();

                mediaPlayerSelect.innerHTML = '<option value="">Select a media player</option>';
                players.forEach(player => {
                    const option = document.createElement('option');
                    option.value = player.entity_id;
                    option.textContent = player.name;
                    mediaPlayerSelect.appendChild(option);
                });
            } catch (error) {
                showStatus('Failed to load media players', 'error');
            }
        }

        async function checkTTSAvailability() {
            try {
                const response = await fetch('/api/voice-replay/tts_config');
                const config = await response.json();

                if (!config.available) {
                    // Hide TTS option if not available
                    const ttsRadio = document.querySelector('input[value="tts"]');
                    const ttsLabel = ttsRadio.closest('.mode-option');
                    ttsLabel.style.display = 'none';

                    // Show a note about TTS not being available
                    const note = document.createElement('p');
                    note.style.color = '#666';
                    note.style.fontSize = '14px';
                    note.style.fontStyle = 'italic';
                    note.textContent = 'Text-to-Speech is not configured in Home Assistant';
                    document.querySelector('.mode-selector').appendChild(note);
                }
            } catch (error) {
                console.warn('Could not check TTS availability:', error);
            }
        }

        // Event listeners
        recordButton.addEventListener('click', toggleRecording);
        playRecordingButton.addEventListener('click', playRecording);
        stopButton.addEventListener('click', stopPlayback);
        generateSpeechButton.addEventListener('click', generateAndPlaySpeech);

        async function toggleRecording() {
            if (!isRecording) {
                await startRecording();
            } else {
                stopRecording();
            }
        }

        async function startRecording() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                recordedChunks = [];

                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        recordedChunks.push(event.data);
                    }
                };

                mediaRecorder.onstop = () => {
                    const blob = new Blob(recordedChunks, { type: 'audio/webm' });
                    const url = URL.createObjectURL(blob);
                    audioPlayback.src = url;
                    audioPlayback.style.display = 'block';
                    playRecordingButton.disabled = false;

                    // Stop all tracks to release microphone
                    stream.getTracks().forEach(track => track.stop());
                };

                mediaRecorder.start();
                isRecording = true;
                recordButton.classList.add('recording');
                recordButton.textContent = '⏹️';
                showStatus('Recording... Click to stop', 'info');

            } catch (error) {
                showStatus('Failed to access microphone', 'error');
            }
        }

        function stopRecording() {
            if (mediaRecorder && isRecording) {
                mediaRecorder.stop();
                isRecording = false;
                recordButton.classList.remove('recording');
                recordButton.textContent = '🎤';
                showStatus('Recording stopped', 'success');
            }
        }

        async function playRecording() {
            const selectedPlayer = mediaPlayerSelect.value;
            if (!selectedPlayer) {
                showStatus('Please select a media player', 'error');
                return;
            }

            if (recordedChunks.length === 0) {
                showStatus('No recording available', 'error');
                return;
            }

            try {
                const blob = new Blob(recordedChunks, { type: 'audio/webm' });
                const formData = new FormData();
                formData.append('audio', blob, 'recording.webm');
                formData.append('entity_id', selectedPlayer);
                formData.append('type', 'recording');

                showStatus('Uploading and playing...', 'info');

                const response = await fetch('/api/voice-replay/upload', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    showStatus('Playing on ' + mediaPlayerSelect.options[mediaPlayerSelect.selectedIndex].text, 'success');
                    stopButton.disabled = false;
                } else {
                    showStatus('Failed to play recording', 'error');
                }
            } catch (error) {
                showStatus('Error: ' + error.message, 'error');
            }
        }

        async function generateAndPlaySpeech() {
            const selectedPlayer = mediaPlayerSelect.value;
            const text = ttsText.value.trim();

            if (!selectedPlayer) {
                showStatus('Please select a media player', 'error');
                return;
            }

            if (!text) {
                showStatus('Please enter some text', 'error');
                return;
            }

            try {
                const formData = new FormData();
                formData.append('text', text);
                formData.append('entity_id', selectedPlayer);
                formData.append('type', 'tts');

                showStatus('Generating speech and playing...', 'info');
                generateSpeechButton.disabled = true;

                const response = await fetch('/api/voice-replay/upload', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    showStatus('Playing speech on ' + mediaPlayerSelect.options[mediaPlayerSelect.selectedIndex].text, 'success');
                    stopButton.disabled = false;
                } else {
                    const errorData = await response.json();
                    showStatus('Failed to generate speech: ' + (errorData.error || 'Unknown error'), 'error');
                }
            } catch (error) {
                showStatus('Error: ' + error.message, 'error');
            } finally {
                generateSpeechButton.disabled = false;
            }
        }

        async function stopPlayback() {
            const selectedPlayer = mediaPlayerSelect.value;
            if (!selectedPlayer) return;

            try {
                await fetch('/api/states/' + selectedPlayer, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ state: 'off' })
                });
                stopButton.disabled = true;
                showStatus('Playback stopped', 'info');
            } catch (error) {
                showStatus('Failed to stop playback', 'error');
            }
        }

        function showStatus(message, type) {
            statusDiv.textContent = message;
            statusDiv.className = 'status ' + type;
            statusDiv.style.display = 'block';

            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 5000);
        }
    </script>
</body>
</html>
        """
        return web.Response(text=html_content, content_type="text/html")


class VoiceReplayUploadView(HomeAssistantView):
    """Handle audio upload and playback."""

    url = UPLOAD_URL
    name = UPLOAD_NAME
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__()
        self.hass = hass

    async def post(self, request: web.Request) -> web.Response:
        """Handle audio upload or text-to-speech and trigger playback."""
        try:
            reader = await request.multipart()

            # Read all form fields
            fields = {}
            while True:
                field = await reader.next()
                if field is None:
                    break

                field_name = field.name
                if field_name in ["audio"]:
                    fields[field_name] = await field.read()
                else:
                    fields[field_name] = (await field.read()).decode()

            entity_id = fields.get("entity_id")
            request_type = fields.get("type", "recording")

            if not entity_id:
                return web.json_response({"error": "Missing entity_id"}, status=400)

            import os
            import tempfile

            if request_type == "tts":
                # Handle text-to-speech
                text = fields.get("text")
                if not text:
                    return web.json_response(
                        {"error": "Missing text for TTS"}, status=400
                    )

                # Use Home Assistant's TTS service
                try:
                    # Call TTS service to speak directly to media player
                    await self.hass.services.async_call(
                        "tts",
                        "speak",
                        {
                            "entity_id": entity_id,
                            "message": text,
                        },
                        blocking=True,
                    )

                    return web.json_response(
                        {"status": "success", "message": "Playing TTS audio"}
                    )

                except Exception as tts_error:
                    _LOGGER.error("TTS service error: %s", tts_error)
                    return web.json_response(
                        {"error": f"TTS service failed: {str(tts_error)}"}, status=500
                    )

            else:
                # Handle audio recording
                audio_data = fields.get("audio")
                if not audio_data:
                    return web.json_response(
                        {"error": "Missing audio data"}, status=400
                    )

                # Save audio temporarily and create a media URL
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".webm"
                ) as tmp_file:
                    tmp_file.write(audio_data)
                    temp_path = tmp_file.name

                # Create a URL that Home Assistant can serve
                media_url = f"/api/{DOMAIN}/media/{os.path.basename(temp_path)}"

                # Store the file path for serving
                self.hass.data.setdefault(DOMAIN, {})
                self.hass.data[DOMAIN][os.path.basename(temp_path)] = temp_path

                # Call the media player service
                await self.hass.services.async_call(
                    "media_player",
                    "play_media",
                    {
                        "entity_id": entity_id,
                        "media_content_id": f"http://localhost:8123{media_url}",
                        "media_content_type": "audio/webm",
                    },
                    blocking=True,
                )

                return web.json_response(
                    {"status": "success", "message": "Playing audio"}
                )

        except Exception as e:
            _LOGGER.error("Error handling upload request: %s", e)
            return web.json_response({"error": str(e)}, status=500)


class VoiceReplayMediaPlayersView(HomeAssistantView):
    """Get available media players."""

    url = MEDIA_PLAYERS_URL
    name = MEDIA_PLAYERS_NAME
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__()
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        """Return list of available media players."""
        media_players = []

        for entity_id, state in self.hass.states.async_all():
            if entity_id.startswith("media_player."):
                media_players.append(
                    {
                        "entity_id": entity_id,
                        "name": state.attributes.get("friendly_name", entity_id),
                        "state": state.state,
                    }
                )

        return web.json_response(media_players)


class VoiceReplayMediaView(HomeAssistantView):
    """Serve temporary audio files."""

    url = f"{MEDIA_URL}/{{filename}}"
    name = MEDIA_NAME
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__()
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        """Serve audio file."""
        filename = request.match_info.get("filename")
        if not filename:
            return web.Response(status=404)

        # Get file path from stored data
        file_path = self.hass.data.get(DOMAIN, {}).get(filename)
        if not file_path:
            return web.Response(status=404)

        try:
            import os

            if not os.path.exists(file_path):
                return web.Response(status=404)

            with open(file_path, "rb") as f:
                content = f.read()

            return web.Response(
                body=content,
                content_type="audio/webm",
                headers={"Content-Disposition": f'inline; filename="{filename}"'},
            )
        except Exception as e:
            _LOGGER.error("Error serving media file %s: %s", filename, e)
            return web.Response(status=500)


class VoiceReplayTTSConfigView(HomeAssistantView):
    """Get TTS configuration and available services."""

    url = TTS_CONFIG_URL
    name = TTS_CONFIG_NAME
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__()
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        """Return TTS configuration."""
        try:
            # Check if TTS is available
            tts_services = []
            if self.hass.services.has_service("tts", "speak"):
                # Get available TTS engines
                tts_domain = self.hass.data.get("tts", {})
                if tts_domain:
                    for service_name in self.hass.services.async_services().get(
                        "tts", {}
                    ):
                        tts_services.append(service_name)
                else:
                    # Fallback - assume basic TTS is available
                    tts_services.append("speak")

            return web.json_response(
                {
                    "available": len(tts_services) > 0,
                    "services": tts_services,
                    "default_service": "speak" if tts_services else None
                }
            )
        except Exception as e:
            _LOGGER.error("Error getting TTS config: %s", e)
            return web.json_response({"available": False, "error": str(e)})


def register_ui_view(hass: HomeAssistant, target_url: str = None) -> None:
    """Register the native UI views."""
    hass.http.register_view(VoiceReplayPanelView())
    hass.http.register_view(VoiceReplayUploadView(hass))
    hass.http.register_view(VoiceReplayMediaPlayersView(hass))
    hass.http.register_view(VoiceReplayMediaView(hass))
    hass.http.register_view(VoiceReplayTTSConfigView(hass))

    _LOGGER.debug("UI views registered - frontend card will be separate repository")
