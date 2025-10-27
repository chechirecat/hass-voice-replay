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


class VoiceReplayPanelView(HomeAssistantView):
    """Serve the native Voice Replay panel HTML."""

    url = PANEL_URL
    name = PANEL_NAME
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        """Serve the Voice Replay panel."""
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Voice Replay</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 20px;
            background: var(--primary-background-color, #fafafa);
            color: var(--primary-text-color, #212121);
        }
        .container { max-width: 600px; margin: 0 auto; }
        .card {
            background: var(--card-background-color, white);
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
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
        select, button {
            padding: 10px;
            margin: 5px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
        }
        button {
            background: #2196f3;
            color: white;
            cursor: pointer;
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
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
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2>🎤 Voice Replay</h2>
            <p>Record audio and play it on your selected media player</p>

            <div>
                <label for="mediaPlayer">Select Media Player:</label>
                <select id="mediaPlayer">
                    <option value="">Loading media players...</option>
                </select>
            </div>

            <button id="recordButton" class="record-button">🎤</button>

            <div>
                <button id="playButton" disabled>▶️ Play Recording</button>
                <button id="stopButton" disabled>⏹️ Stop</button>
            </div>

            <div id="status" class="status" style="display: none;"></div>

            <audio id="audioPlayback" controls style="width: 100%; margin-top: 10px; display: none;"></audio>
        </div>
    </div>

    <script>
        let mediaRecorder;
        let recordedChunks = [];
        let isRecording = false;

        const recordButton = document.getElementById('recordButton');
        const playButton = document.getElementById('playButton');
        const stopButton = document.getElementById('stopButton');
        const mediaPlayerSelect = document.getElementById('mediaPlayer');
        const statusDiv = document.getElementById('status');
        const audioPlayback = document.getElementById('audioPlayback');

        // Load media players on page load
        loadMediaPlayers();

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

        recordButton.addEventListener('click', toggleRecording);
        playButton.addEventListener('click', playRecording);
        stopButton.addEventListener('click', stopPlayback);

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
                    playButton.disabled = false;

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
        """Handle audio upload and trigger playback."""
        try:
            reader = await request.multipart()
            audio_field = await reader.next()
            entity_id_field = await reader.next()

            if not audio_field or not entity_id_field:
                return web.json_response({"error": "Missing audio or entity_id"}, status=400)

            audio_data = await audio_field.read()
            entity_id = (await entity_id_field.read()).decode()

            # Save audio temporarily and create a media URL
            import os
            import tempfile

            with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp_file:
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

            return web.json_response({"status": "success", "message": "Playing audio"})

        except Exception as e:
            _LOGGER.error("Error handling audio upload: %s", e)
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
                media_players.append({
                    "entity_id": entity_id,
                    "name": state.attributes.get("friendly_name", entity_id),
                    "state": state.state
                })

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
        filename = request.match_info.get('filename')
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

            with open(file_path, 'rb') as f:
                content = f.read()

            return web.Response(
                body=content,
                content_type='audio/webm',
                headers={'Content-Disposition': f'inline; filename="{filename}"'}
            )
        except Exception as e:
            _LOGGER.error("Error serving media file %s: %s", filename, e)
            return web.Response(status=500)


def register_ui_view(hass: HomeAssistant, target_url: str = None) -> None:
    """Register the native UI views."""
    hass.http.register_view(VoiceReplayPanelView())
    hass.http.register_view(VoiceReplayUploadView(hass))
    hass.http.register_view(VoiceReplayMediaPlayersView(hass))
    hass.http.register_view(VoiceReplayMediaView(hass))
