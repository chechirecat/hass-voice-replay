"""Voice Replay integration - minimal skeleton."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, SERVICE_REPLAY, DATA_KEY

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration from YAML (not used)."""
    hass.data.setdefault(DOMAIN, {})

    # Register service for YAML installs (available immediately after restart).
    _register_replay_service(hass)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(DATA_KEY, {})

    # Ensure service is registered (no double registration).
    _register_replay_service(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Remove service (safe even if registered during YAML setup).
    hass.services.async_remove(DOMAIN, SERVICE_REPLAY)
    return True


# New helper placed at bottom of file to avoid code duplication.
def _register_replay_service(hass: HomeAssistant) -> None:
    """Register the replay service if not already registered."""
    if hass.services.has_service(DOMAIN, SERVICE_REPLAY):
        return

    async def handle_replay(call: ServiceCall) -> None:
        """Handle the replay service call."""
        # Minimal stub: store last call data for tests or other components.
        payload: dict[str, Any] = {
            "url": call.data.get("url"),
            "media_content": call.data.get("media_content"),
            "entity_id": call.data.get("entity_id"),
        }
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN].setdefault(DATA_KEY, {})
        hass.data[DOMAIN][DATA_KEY]["last_replay"] = payload
        _LOGGER.info("voice_replay.replay called: %s", payload)

    hass.services.async_register(DOMAIN, SERVICE_REPLAY, handle_replay)
        entity_id = call.data.get("entity_id")
        message = call.data.get("message", "Tap to record and send audio")
        ttl = int(call.data.get("ttl", TOKEN_TTL_SECONDS))

        token = _gen_token()
        expires = time.time() + ttl
        hass.data[DOMAIN][DATA_TOKENS][token] = {
            "entity_id": entity_id,
            "expires": expires,
            "created": time.time(),
        }

        base = get_url(hass, allow_internal=True)
        record_url = f"{base}/api/voice_replay/record?token={token}"

        notify_service = f"mobile_app_{device_id}"
        try:
            await hass.services.async_call(
                "notify",
                notify_service,
                {"message": f"{message}\n\n{record_url}"},
                blocking=True,
            )
            hass.logger.info("Sent recording request to %s (token %s)", notify_service, token)
        except Exception as exc:  # pylint: disable=broad-except
            hass.logger.error("Failed to send notify to %s: %s", notify_service, exc)

        hass.loop.call_later(ttl + 5, lambda: hass.async_create_task(_cleanup_token(hass, token)))

    hass.services.async_register(DOMAIN, "request_recording", handle_request_recording)

    return True


async def _cleanup_token(hass: HomeAssistant, token: str):
    tokens = hass.data[DOMAIN][DATA_TOKENS]
    if token in tokens:
        if tokens[token]["expires"] < time.time():
            tokens.pop(token, None)


class RecordPageView(HomeAssistantView):
    url = "/api/voice_replay/record"
    name = "api:voice_replay:record"
    requires_auth = False  # we validate the token explicitly

    def __init__(self, hass: HomeAssistantType):
        super().__init__()
        self.hass = hass

    async def get(self, request):
        hass = self.hass
        token = request.args.get("token")
        if not token:
            return self.json_message("Missing token", status=400)

        tokens: Dict = hass.data[DOMAIN][DATA_TOKENS]
        token_data = tokens.get(token)
        if not token_data or token_data.get("expires", 0) < time.time():
            return self.json_message("Invalid or expired token", status=403)

        html = _RECORD_PAGE_HTML.format(token=token)
        return self.response(html, content_type="text/html")


class UploadView(HomeAssistantView):
    url = "/api/voice_replay/upload"
    name = "api:voice_replay:upload"
    requires_auth = False  # token-based validation

    def __init__(self, hass: HomeAssistantType):
        super().__init__()
        self.hass = hass

    async def post(self, request):
        hass = self.hass
        token = request.args.get("token")
        if not token:
            return self.json_message("Missing token", status=400)

        tokens: Dict = hass.data[DOMAIN][DATA_TOKENS]
        token_data = tokens.get(token)
        if not token_data or token_data.get("expires", 0) < time.time():
            return self.json_message("Invalid or expired token", status=403)

        try:
            post = await request.post()
        except Exception as exc:
            hass.logger.exception("Failed to parse upload POST: %s", exc)
            return self.json_message("Failed to parse upload", status=400)

        if "file" not in post:
            return self.json_message("Missing file", status=400)

        upload_file = post["file"]  # this is an UploadedFile object
        filename_in = getattr(upload_file, "filename", None) or "recording"
        entity_id = post.get("entity_id") or token_data.get("entity_id")
        if not entity_id:
            return self.json_message("No entity_id specified for playback", status=400)

        try:
            duration = float(post.get("duration", 5.0))
        except Exception:
            duration = 5.0

        www_path = os.path.join(hass.config.path("www"), WWW_SUBPATH)
        os.makedirs(www_path, exist_ok=True)

        base_name = slugify(os.path.splitext(filename_in)[0]) or "recording"
        unique = f"{base_name}-{uuid.uuid4().hex[:8]}"
        saved_name = f"{unique}{os.path.splitext(filename_in)[1] or '.webm'}"
        saved_path = os.path.join(www_path, saved_name)

        try:
            with open(saved_path, "wb") as fh:
                uploaded_fp = upload_file.file
                uploaded_fp.seek(0)
                while True:
                    chunk = uploaded_fp.read(65536)
                    if not chunk:
                        break
                    fh.write(chunk)
        except Exception as exc:
            hass.logger.exception("Failed to save uploaded recording: %s", exc)
            return self.json_message("Failed to save file", status=500)

        final_name = saved_name
        ffmpeg_bin = shutil_which("ffmpeg")
        if ffmpeg_bin:
            trans_name = f"{unique}.mp3"
            trans_path = os.path.join(www_path, trans_name)
            try:
                subprocess.run(
                    [ffmpeg_bin, "-y", "-i", saved_path, "-ar", "22050", "-ac", "1", trans_path],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                final_name = trans_name
                try:
                    os.remove(saved_path)
                except Exception:
                    pass
            except Exception as exc:
                hass.logger.warning("ffmpeg transcode failed or ffmpeg not available: %s", exc)
        else:
            hass.logger.debug("ffmpeg not found; will use uploaded file as-is")

        base = get_url(hass, allow_internal=True)
        media_url = f"{base}/local/{WWW_SUBPATH}/{final_name}"

        try:
            state = hass.states.get(entity_id)
            was_playing = state and state.state == STATE_PLAYING
            hass.data[DOMAIN][DATA_PENDING][entity_id] = {
                "was_playing": was_playing,
                "triggered_at": time.time(),
            }
            await hass.services.async_call(
                "media_player",
                "media_pause",
                {ATTR_ENTITY_ID: entity_id},
                blocking=True,
            )
        except Exception as exc:
            hass.logger.debug("Error while pausing media_player %s: %s", entity_id, exc)

        try:
            await hass.services.async_call(
                "media_player",
                "play_media",
                {
                    ATTR_ENTITY_ID: entity_id,
                    "media_content_id": media_url,
                    "media_content_type": "music",
                },
                blocking=True,
            )
        except Exception as exc:
            hass.logger.exception("Failed to call play_media on %s: %s", entity_id, exc)
            return self.json_message(f"Failed to play media on {entity_id}", status=500)

        async def _resume_cb(now):
            try:
                pending = hass.data[DOMAIN][DATA_PENDING].pop(entity_id, None)
                if pending and pending.get("was_playing"):
                    await hass.services.async_call(
                        "media_player",
                        "media_play",
                        {ATTR_ENTITY_ID: entity_id},
                        blocking=True,
                    )
            except Exception as exc:  # pylint: disable=broad-except
                hass.logger.exception("Error resuming media_player %s: %s", entity_id, exc)

        hass_event.async_call_later(hass, duration + 0.5, _resume_cb)

        tokens.pop(token, None)

        return self.json({"url": media_url, "duration": duration})


def shutil_which(cmd: str):
    import shutil

    try:
        return shutil.which(cmd)
    except Exception:
        return None


_RECORDED_JS = r"""
<script>
const token = "{token}";
const uploadUrl = `/api/voice_replay/upload?token=${token}`;

let mediaRecorder;
let recordedChunks = [];
let startTime;

async function startRecording() {
  recordedChunks = [];
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
  let opts = {mimeType: 'audio/webm'};
  if (MediaRecorder.isTypeSupported('audio/wav')) {
    opts = {mimeType: 'audio/wav'};
  } else if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
    opts = {mimeType: 'audio/webm;codecs=opus'};
  } else if (MediaRecorder.isTypeSupported('audio/ogg')) {
    opts = {mimeType: 'audio/ogg'};
  }
  mediaRecorder = new MediaRecorder(stream, opts);
  mediaRecorder.ondataavailable = (e) => {
    if (e.data && e.data.size > 0) {
      recordedChunks.push(e.data);
    }
  };
  mediaRecorder.onstop = onRecordingStop;
  mediaRecorder.start();
  startTime = Date.now();
  document.getElementById('status').textContent = 'Recording...';
  document.getElementById('startBtn').disabled = true;
  document.getElementById('stopBtn').disabled = false;
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
    document.getElementById('status').textContent = 'Processing...';
    document.getElementById('stopBtn').disabled = true;
  }
}

async function onRecordingStop() {
  const endTime = Date.now();
  const durationSec = Math.round((endTime - startTime) / 1000);
  const blob = new Blob(recordedChunks, { type: recordedChunks[0].type || 'audio/webm' });
  const fd = new FormData();
  fd.append('file', blob, 'recording.' + (blob.type.includes('wav') ? 'wav' : (blob.type.includes('mp3') ? 'mp3' : 'webm')));
  fd.append('duration', String(durationSec));
  try {
    const resp = await fetch(uploadUrl, { method: 'POST', body: fd });
    if (resp.ok) {
      const j = await resp.json();
      document.getElementById('status').textContent = 'Uploaded. Playing on device.';
      document.getElementById('result').textContent = 'Media URL: ' + j.url;
    } else {
      const txt = await resp.text();
      document.getElementById('status').textContent = 'Upload failed: ' + txt;
    }
  } catch (err) {
    document.getElementById('status').textContent = 'Error uploading: ' + err;
  } finally {
    document.getElementById('startBtn').disabled = false;
  }
}
</script>
"""

_RECORD_PAGE_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Voice Replay — Record</title>
</head>
<body>
  <h2>Record a short message</h2>
  <p id="status">Idle</p>
  <button id="startBtn" onclick="startRecording()">Start recording</button>
  <button id="stopBtn" onclick="stopRecording()" disabled>Stop</button>
  <p id="result"></p>
  {js}
</body>
</html>
""".format(js=_RECORDED_JS)
