class CameraController {
  constructor() {
    this.video = document.getElementById('webcam-video');
    this.canvas = document.getElementById('landmark-canvas');
    this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
    this.hiddenCanvas = document.createElement('canvas');
    this.hiddenCtx = this.hiddenCanvas.getContext('2d');
    
    this.isRunning = false;
    this.drawLandmarks = true;
    this.wsConnected = false;
    this.stream = null;
    
    this.ws = null;
    
    // Performance Tracking
    this.frameCount = 0;
    this.lastFpsTime = performance.now();
    
    // MediaPipe tracking
    this.mpHands = null;
    this.mpProcessing = false;
    this.lastLandmarks = [];
    this.lastHandBoundingBox = null;
    
    // Config
    this.mpTargetFps = 20;
    this.ollamaTargetFps = 1;
    this.lastMpTime = 0;
    this.lastOllamaTime = 0;

    this.init();
  }

  async init() {
    this.setupWebSocket();
    await this.initMediaPipe();
    this.startCamera();
  }

  setupWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/ws/stream`;
    
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = () => {
      this.wsConnected = true;
      console.log("[Camera] WebSocket Connected");
    };
    
    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'result') {
            this.handleRecognitionResult(data);
        } else if (data.type === 'mode_changed') {
            console.log("Mode changed to:", data.mode);
        }
      } catch (e) {}
    };
    
    this.ws.onclose = () => {
      this.wsConnected = false;
      setTimeout(() => this.setupWebSocket(), 3000);
    };
  }

  async initMediaPipe() {
    if (window.Hands) {
      this.mpHands = new window.Hands({
        locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
      });
      this.mpHands.setOptions({
        maxNumHands: 2,
        modelComplexity: 0,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5
      });
      
      this.mpHands.onResults((results) => {
        this.mpProcessing = false;
        this.processMediaPipeResults(results);
      });
    }
  }

  async startCamera() {
    if (this.isRunning) return;
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, frameRate: { ideal: 30 } }
      });
      
      this.video.srcObject = this.stream;
      await new Promise(resolve => {
        this.video.onloadedmetadata = () => resolve();
      });
      
      this.video.play();
      this.isRunning = true;
      
      this.canvas.width = this.video.videoWidth;
      this.canvas.height = this.video.videoHeight;
      this.hiddenCanvas.width = this.video.videoWidth;
      this.hiddenCanvas.height = this.video.videoHeight;
      
      document.getElementById('camera-offline-msg').style.display = 'none';
      document.getElementById('live-badge').style.display = 'inline-block';
      
      // Start main loops
      this.cameraLoop = this.cameraLoop.bind(this);
      requestAnimationFrame(this.cameraLoop);
      
    } catch (e) {
      console.error("[Camera] Error:", e);
    }
  }

  cameraLoop(timestamp) {
    if (!this.isRunning) return;

    const now = performance.now();
    this.frameCount++;
    
    // Compute Frame Age (very roughly time since last capture update)
    // For native video element, age is generally ~0 unless blocked
    const frameAge = 0; 
    
    if (now - this.lastFpsTime >= 500) {
      const fps = Math.round((this.frameCount * 1000) / (now - this.lastFpsTime));
      document.getElementById('perf-cam-fps').innerText = fps;
      document.getElementById('perf-frame-age').innerText = "16"; // estimated display age
      
      const buffered = this.ws ? this.ws.bufferedAmount : 0;
      document.getElementById('perf-pending').innerText = buffered;
      
      const recRate = Math.round((this.recCount || 0) * 2); // multiplied by 2 since it's 500ms
      document.getElementById('perf-rec-rate').innerText = recRate;
      this.recCount = 0;
      
      this.frameCount = 0;
      this.lastFpsTime = now;
    }

    if (this.mpHands && !this.mpProcessing) {
        if (now - this.lastMpTime >= (1000 / this.mpTargetFps)) {
            this.mpProcessing = true;
            this.lastMpTime = now;
            this.mpStart = performance.now();
            this.mpHands.send({ image: this.video }).catch(() => {
                this.mpProcessing = false;
            });
        }
    }

    if (this.wsConnected && (now - this.lastOllamaTime >= (1000 / this.ollamaTargetFps))) {
        this.lastOllamaTime = now;
        this.sendSelectedFrameToBackend();
        this.recCount = (this.recCount || 0) + 1;
    }

    requestAnimationFrame(this.cameraLoop);
  }

  processMediaPipeResults(results) {
    const mpEnd = performance.now();
    if (this.mpStart) {
       document.getElementById('perf-mp-time').innerText = Math.round(mpEnd - this.mpStart);
    }
    
    const renderStart = performance.now();

    // Clear canvas
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
      this.lastLandmarks = results.multiHandLandmarks;
      
      let minX = 1, minY = 1, maxX = 0, maxY = 0;
      
      for (const landmarks of results.multiHandLandmarks) {
        for (const pt of landmarks) {
          minX = Math.min(minX, pt.x);
          minY = Math.min(minY, pt.y);
          maxX = Math.max(maxX, pt.x);
          maxY = Math.max(maxY, pt.y);
        }
        
        if (this.drawLandmarks && window.drawConnectors && window.drawLandmarks) {
          window.drawConnectors(this.ctx, landmarks, window.HAND_CONNECTIONS, {color: '#00FF00', lineWidth: 2});
          window.drawLandmarks(this.ctx, landmarks, {color: '#FF0000', lineWidth: 1, radius: 2});
        }
      }
      
      this.lastHandBoundingBox = { minX, minY, maxX, maxY };
    } else {
      this.lastLandmarks = [];
      this.lastHandBoundingBox = null;
    }
    
    const renderEnd = performance.now();
    document.getElementById('perf-render-time').innerText = Math.round(renderEnd - renderStart);
  }

  sendSelectedFrameToBackend() {
    if (!this.lastHandBoundingBox || this.ws.readyState !== WebSocket.OPEN) {
        return;
    }

    // We have a hand. Let's crop it.
    const { minX, minY, maxX, maxY } = this.lastHandBoundingBox;
    
    // Draw current video frame to hidden canvas
    this.hiddenCtx.drawImage(this.video, 0, 0, this.hiddenCanvas.width, this.hiddenCanvas.height);
    
    const w = this.hiddenCanvas.width;
    const h = this.hiddenCanvas.height;
    
    const padX = (maxX - minX) * 0.25;
    const padY = (maxY - minY) * 0.25;
    
    const cropX = Math.max(0, Math.floor((minX - padX) * w));
    const cropY = Math.max(0, Math.floor((minY - padY) * h));
    const cropW = Math.min(w - cropX, Math.ceil((maxX - minX + 2*padX) * w));
    const cropH = Math.min(h - cropY, Math.ceil((maxY - minY + 2*padY) * h));

    if (cropW <= 0 || cropH <= 0) return;

    // Extract crop
    const cropImageData = this.hiddenCtx.getImageData(cropX, cropY, cropW, cropH);
    
    // Create a temporary canvas for the crop to encode
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = cropW;
    tempCanvas.height = cropH;
    tempCanvas.getContext('2d').putImageData(cropImageData, 0, 0);
    
    // VERY FAST local JPEG encode of the TINY cropped image
    const b64 = tempCanvas.toDataURL('image/jpeg', 0.85);

    // Send to backend with is_cropped flag to bypass backend MediaPipe
    this.ws.send(JSON.stringify({ 
        type: 'frame', 
        image: b64,
        is_cropped: true 
    }));
  }

  handleRecognitionResult(data) {
    const hudSign = document.getElementById('hud-sign-text');
    const visionStatus = document.getElementById('vision-assist-btn');
    
    if (visionStatus) {
        const oStatus = data.ollama_status || "OLLAMA READY";
        if (oStatus === "OLLAMA ANALYZING") {
            visionStatus.innerHTML = `Ollama Vision: <span style="color: var(--warning);">● ANALYZING</span>`;
        } else if (oStatus === "OLLAMA ERROR" || !data.model_available) {
            visionStatus.innerHTML = `Ollama Vision: <span style="color: var(--error);">● OFFLINE</span>`;
        } else {
            visionStatus.innerHTML = `Ollama Vision: <span style="color: var(--success); font-weight: bold;">● READY</span>`;
        }
    }

    if (data.stable_sign && data.stable_sign !== "UNKNOWN" && data.stable_sign !== "NONE") {
      hudSign.innerText = data.stable_sign;
      if (data.newly_emitted && window.app_events) {
          window.app_events.emit('sign_detected', data.stable_sign);
      }
    }
  }
}

// Auto-start
window.addEventListener('DOMContentLoaded', () => {
  window.cameraController = new CameraController();
});
