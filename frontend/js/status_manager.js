/**
 * System Status Manager
 * Polls backend health and updates UI indicators
 */

class StatusManager {
  constructor() {
    this.pollInterval = 5000;
    this.timer = null;
    this.healthData = null;
  }

  init() {
    this.checkHealth();
    this.timer = setInterval(() => this.checkHealth(), this.pollInterval);
  }

  async checkHealth() {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        this.healthData = await res.json();
        this.renderStatus(this.healthData);
      } else {
        this.renderError();
      }
    } catch (e) {
      this.renderError();
    }
  }

  renderStatus(data) {
    // Camera
    const camEl = document.getElementById('status-camera');
    const isCamRunning = window.SignBridgeApp && window.SignBridgeApp.camera && window.SignBridgeApp.camera.isRunning;
    if (isCamRunning) {
      camEl.className = 'pill-badge active-green';
      camEl.innerHTML = '<span class="dot green"></span> Camera: Active';
    } else if (data.camera && data.camera.connected) {
      camEl.className = 'pill-badge';
      camEl.innerHTML = '<span class="dot yellow"></span> Camera: Standby';
    } else {
      camEl.className = 'pill-badge active-red';
      camEl.innerHTML = '<span class="dot red"></span> Camera: Offline';
    }

    // ASL Model
    const aslEl = document.getElementById('status-asl');
    if (data.models && data.models.asl && data.models.asl.available) {
      aslEl.className = 'pill-badge active-green';
      aslEl.innerHTML = '<span class="dot green"></span> ASL: Loaded';
    } else {
      aslEl.className = 'pill-badge active-red';
      aslEl.innerHTML = '<span class="dot red"></span> ASL: Not Loaded';
    }

    // ISL Model
    const islEl = document.getElementById('status-isl');
    if (data.models && data.models.isl && data.models.isl.available) {
      islEl.className = 'pill-badge active-green';
      islEl.innerHTML = '<span class="dot green"></span> ISL: Loaded';
    } else {
      islEl.className = 'pill-badge active-red';
      islEl.innerHTML = '<span class="dot red"></span> ISL: Not Loaded';
    }

    // Ollama
    const ollamaEl = document.getElementById('status-ollama');
    if (data.ollama && data.ollama.running) {
      ollamaEl.className = 'pill-badge active-green';
      ollamaEl.innerHTML = `<span class="dot green"></span> Ollama: ${data.ollama.translation_model || 'Ready'}`;
    } else {
      ollamaEl.className = 'pill-badge active-yellow';
      ollamaEl.innerHTML = '<span class="dot yellow"></span> Ollama: Offline (Local Fallback)';
    }

    // TTS
    const ttsEl = document.getElementById('status-tts');
    ttsEl.className = 'pill-badge active-green';
    ttsEl.innerHTML = '<span class="dot green"></span> TTS: Ready';

    // Avatar
    const avatarEl = document.getElementById('status-avatar');
    avatarEl.className = 'pill-badge active-green';
    avatarEl.innerHTML = '<span class="dot green"></span> 3D: Ready';
  }

  renderError() {
    const ids = ['status-asl', 'status-isl', 'status-ollama'];
    ids.forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        el.className = 'pill-badge active-red';
        el.innerHTML = '<span class="dot red"></span> Backend Offline';
      }
    });
  }
}

window.StatusManager = StatusManager;
