// Voice Replay Card - Custom Lovelace Card
// A beautiful card for recording voice messages and text-to-speech

const LitElement = customElements.get("home-assistant-main")
  ? Object.getPrototypeOf(customElements.get("home-assistant-main"))
  : Object.getPrototypeOf(customElements.get("hui-view"));
const html = LitElement.prototype.html;
const css = LitElement.prototype.css;

class VoiceReplayCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object },
      _mediaPlayers: { type: Array },
      _selectedPlayer: { type: String },
      _mode: { type: String },
      _isRecording: { type: Boolean },
      _recordedChunks: { type: Array },
      _mediaRecorder: { type: Object },
      _status: { type: String },
      _statusType: { type: String },
      _ttsText: { type: String },
    };
  }

  constructor() {
    super();
    this._mediaPlayers = [];
    this._selectedPlayer = '';
    this._mode = 'record';
    this._isRecording = false;
    this._recordedChunks = [];
    this._mediaRecorder = null;
    this._status = '';
    this._statusType = '';
    this._ttsText = '';
  }

  static get styles() {
    return css`
      ha-card {
        padding: 16px;
        --mdc-icon-size: 24px;
      }
      
      .card-header {
        font-size: 16px;
        font-weight: 500;
        padding-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
      }
      
      .card-header ha-icon {
        --mdc-icon-size: 20px;
        color: var(--primary-color);
      }
      
      .media-player-select {
        margin-bottom: 16px;
      }
      
      .media-player-select label {
        display: block;
        margin-bottom: 4px;
        font-weight: 500;
        color: var(--primary-text-color);
      }
      
      select {
        width: 100%;
        padding: 8px 12px;
        border: 1px solid var(--divider-color);
        border-radius: var(--ha-card-border-radius, 8px);
        background: var(--card-background-color);
        color: var(--primary-text-color);
        font-size: 14px;
      }
      
      .mode-selector {
        display: flex;
        gap: 16px;
        margin-bottom: 20px;
        justify-content: center;
      }
      
      .mode-option {
        display: flex;
        align-items: center;
        gap: 6px;
        cursor: pointer;
        padding: 8px 12px;
        border-radius: var(--ha-card-border-radius, 8px);
        transition: background-color 0.2s;
        font-size: 14px;
      }
      
      .mode-option:hover {
        background-color: var(--secondary-background-color);
      }
      
      .mode-option input[type="radio"] {
        margin: 0;
      }
      
      .section {
        margin: 16px 0;
        padding: 16px;
        border-radius: var(--ha-card-border-radius, 8px);
        background: var(--secondary-background-color);
      }
      
      .section.hidden {
        display: none;
      }
      
      .section h3 {
        margin: 0 0 12px 0;
        font-size: 14px;
        font-weight: 500;
        color: var(--primary-text-color);
      }
      
      .record-button {
        background: var(--error-color, #ff5722);
        color: white;
        border: none;
        border-radius: 50%;
        width: 64px;
        height: 64px;
        font-size: 24px;
        cursor: pointer;
        margin: 16px auto;
        display: block;
        transition: all 0.2s ease;
        box-shadow: var(--ha-card-box-shadow, 0 2px 4px rgba(0,0,0,0.1));
      }
      
      .record-button:hover {
        transform: scale(1.05);
        box-shadow: var(--ha-card-box-shadow, 0 4px 8px rgba(0,0,0,0.15));
      }
      
      .record-button.recording {
        background: var(--error-color, #f44336);
        animation: pulse 1s infinite;
      }
      
      @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
      }
      
      button {
        padding: 8px 16px;
        margin: 4px;
        border: none;
        border-radius: var(--ha-card-border-radius, 8px);
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
        background: var(--primary-color);
        color: var(--text-primary-color, white);
      }
      
      button:hover:not(:disabled) {
        background: var(--dark-primary-color);
        transform: translateY(-1px);
      }
      
      button:disabled {
        background: var(--disabled-color);
        color: var(--disabled-text-color);
        cursor: not-allowed;
        transform: none;
      }
      
      .tts-button {
        background: var(--success-color, #4caf50);
      }
      
      .tts-button:hover:not(:disabled) {
        background: #388e3c;
      }
      
      textarea {
        width: 100%;
        min-height: 80px;
        padding: 12px;
        border: 1px solid var(--divider-color);
        border-radius: var(--ha-card-border-radius, 8px);
        background: var(--card-background-color);
        color: var(--primary-text-color);
        font-family: inherit;
        font-size: 14px;
        resize: vertical;
        box-sizing: border-box;
      }
      
      textarea:focus {
        outline: none;
        border-color: var(--primary-color);
      }
      
      .status {
        padding: 8px 12px;
        margin: 12px 0;
        border-radius: var(--ha-card-border-radius, 8px);
        text-align: center;
        font-size: 14px;
        font-weight: 500;
      }
      
      .status.success { 
        background: var(--success-color, #c8e6c9); 
        color: var(--success-text-color, #2e7d32); 
      }
      
      .status.error { 
        background: var(--error-color, #ffcdd2); 
        color: var(--error-text-color, #c62828); 
      }
      
      .status.info { 
        background: var(--info-color, #bbdefb); 
        color: var(--info-text-color, #1565c0); 
      }
      
      .control-group {
        display: flex;
        gap: 8px;
        align-items: center;
        flex-wrap: wrap;
        justify-content: center;
      }

      .empty-state {
        text-align: center;
        padding: 32px 16px;
        color: var(--secondary-text-color);
      }

      .empty-state ha-icon {
        --mdc-icon-size: 48px;
        color: var(--disabled-color);
        margin-bottom: 16px;
      }
    `;
  }

  setConfig(config) {
    if (!config) {
      throw new Error('Invalid configuration');
    }
    this.config = config;
  }

  firstUpdated() {
    this._loadMediaPlayers();
    this._checkTTSAvailability();
    
    // Set default player from config
    if (this.config.entity) {
      this._selectedPlayer = this.config.entity;
    }
  }

  updated(changedProps) {
    if (changedProps.has('hass') && this.hass) {
      this._loadMediaPlayers();
    }
  }

  async _loadMediaPlayers() {
    if (!this.hass) return;
    
    try {
      // Get media players from Home Assistant states
      const mediaPlayers = [];
      Object.keys(this.hass.states).forEach(entityId => {
        if (entityId.startsWith('media_player.')) {
          const state = this.hass.states[entityId];
          mediaPlayers.push({
            entity_id: entityId,
            name: state.attributes.friendly_name || entityId,
            state: state.state
          });
        }
      });
      
      this._mediaPlayers = mediaPlayers;
      this.requestUpdate();
    } catch (error) {
      this._showStatus('Failed to load media players', 'error');
    }
  }

  async _checkTTSAvailability() {
    // Check if TTS service is available
    if (this.hass && this.hass.services.tts) {
      // TTS is available
      return true;
    }
    return false;
  }

  _showStatus(message, type) {
    this._status = message;
    this._statusType = type;
    this.requestUpdate();
    
    setTimeout(() => {
      this._status = '';
      this.requestUpdate();
    }, 5000);
  }

  async _startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this._mediaRecorder = new MediaRecorder(stream);
      this._recordedChunks = [];

      this._mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this._recordedChunks.push(event.data);
        }
      };

      this._mediaRecorder.onstop = () => {
        stream.getTracks().forEach(track => track.stop());
        this._isRecording = false;
        this.requestUpdate();
      };

      this._mediaRecorder.start();
      this._isRecording = true;
      this._showStatus('Recording... Click to stop', 'info');
      this.requestUpdate();
    } catch (error) {
      this._showStatus('Failed to access microphone. Please check permissions.', 'error');
    }
  }

  _stopRecording() {
    if (this._mediaRecorder && this._isRecording) {
      this._mediaRecorder.stop();
      this._showStatus('Recording stopped', 'success');
    }
  }

  async _playRecording() {
    if (!this._selectedPlayer) {
      this._showStatus('Please select a media player', 'error');
      return;
    }

    if (this._recordedChunks.length === 0) {
      this._showStatus('No recording available', 'error');
      return;
    }

    try {
      const blob = new Blob(this._recordedChunks, { type: 'audio/webm' });
      const formData = new FormData();
      formData.append('audio', blob, 'recording.webm');
      formData.append('entity_id', this._selectedPlayer);
      formData.append('type', 'recording');

      this._showStatus('Uploading and playing...', 'info');

      const response = await fetch('/api/voice-replay/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.hass.auth.accessToken}`
        },
        body: formData
      });

      if (response.ok) {
        const playerName = this._mediaPlayers.find(p => p.entity_id === this._selectedPlayer)?.name || this._selectedPlayer;
        this._showStatus(`Playing on ${playerName}`, 'success');
      } else {
        this._showStatus('Failed to play recording', 'error');
      }
    } catch (error) {
      this._showStatus(`Error: ${error.message}`, 'error');
    }
  }

  async _generateAndPlaySpeech() {
    if (!this._selectedPlayer) {
      this._showStatus('Please select a media player', 'error');
      return;
    }

    if (!this._ttsText.trim()) {
      this._showStatus('Please enter some text', 'error');
      return;
    }

    try {
      // Use Home Assistant's built-in TTS service
      await this.hass.callService('tts', 'speak', {
        entity_id: this._selectedPlayer,
        message: this._ttsText
      });

      const playerName = this._mediaPlayers.find(p => p.entity_id === this._selectedPlayer)?.name || this._selectedPlayer;
      this._showStatus(`Playing speech on ${playerName}`, 'success');
    } catch (error) {
      this._showStatus(`Error: ${error.message}`, 'error');
    }
  }

  render() {
    if (!this.hass) {
      return html`
        <ha-card>
          <div class="empty-state">
            <ha-icon icon="mdi:loading"></ha-icon>
            <div>Loading...</div>
          </div>
        </ha-card>
      `;
    }

    if (this._mediaPlayers.length === 0) {
      return html`
        <ha-card>
          <div class="card-header">
            <ha-icon icon="mdi:microphone"></ha-icon>
            ${this.config.title || 'Voice Replay'}
          </div>
          <div class="empty-state">
            <ha-icon icon="mdi:speaker-off"></ha-icon>
            <div>No media players found</div>
            <div style="font-size: 12px; margin-top: 8px;">
              Make sure you have media players configured in Home Assistant
            </div>
          </div>
        </ha-card>
      `;
    }

    return html`
      <ha-card>
        ${this.config.show_title !== false ? html`
          <div class="card-header">
            <ha-icon icon="mdi:microphone"></ha-icon>
            ${this.config.title || 'Voice Replay'}
          </div>
        ` : ''}

        <div class="media-player-select">
          <label>Select Media Player:</label>
          <select 
            @change=${(e) => { this._selectedPlayer = e.target.value; }}
            .value=${this._selectedPlayer}
          >
            <option value="">Choose a media player...</option>
            ${this._mediaPlayers.map(player => html`
              <option 
                value="${player.entity_id}"
                ?selected=${player.entity_id === this._selectedPlayer}
              >
                ${player.name}
              </option>
            `)}
          </select>
        </div>

        <div class="mode-selector">
          <label class="mode-option">
            <input 
              type="radio" 
              name="mode" 
              value="record" 
              .checked=${this._mode === 'record'}
              @change=${() => { this._mode = 'record'; }}
            >
            <span>🎤 Record Voice</span>
          </label>
          <label class="mode-option">
            <input 
              type="radio" 
              name="mode" 
              value="tts"
              .checked=${this._mode === 'tts'}
              @change=${() => { this._mode = 'tts'; }}
            >
            <span>🗣️ Text-to-Speech</span>
          </label>
        </div>

        <div class="section ${this._mode !== 'record' ? 'hidden' : ''}">
          <h3>Voice Recording</h3>
          <button 
            class="record-button ${this._isRecording ? 'recording' : ''}"
            @click=${this._isRecording ? this._stopRecording : this._startRecording}
          >
            ${this._isRecording ? '⏹️' : '🎤'}
          </button>
          <div class="control-group">
            <button 
              @click=${this._playRecording} 
              ?disabled=${this._recordedChunks.length === 0}
            >
              ▶️ Play Recording
            </button>
          </div>
        </div>

        <div class="section ${this._mode !== 'tts' ? 'hidden' : ''}">
          <h3>Text-to-Speech</h3>
          <textarea 
            placeholder="Enter the text you want to convert to speech..."
            .value=${this._ttsText}
            @input=${(e) => { this._ttsText = e.target.value; }}
          ></textarea>
          <div class="control-group">
            <button class="tts-button" @click=${this._generateAndPlaySpeech}>
              🗣️ Generate & Play Speech
            </button>
          </div>
        </div>

        ${this._status ? html`
          <div class="status ${this._statusType}">
            ${this._status}
          </div>
        ` : ''}
      </ha-card>
    `;
  }

  getCardSize() {
    return 4;
  }
}

// Register the card
customElements.define('voice-replay-card', VoiceReplayCard);

// Add to card picker
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'voice-replay-card',
  name: 'Voice Replay Card',
  description: 'A card for recording voice messages and text-to-speech'
});

// Version info for HACS
console.info(
  `%c  VOICE-REPLAY-CARD  %c  Version 0.8.0  `,
  'color: orange; font-weight: bold; background: black',
  'color: white; font-weight: bold; background: dimgray',
);