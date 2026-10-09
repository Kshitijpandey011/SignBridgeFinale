class ContinuousVisionAnalyzer {
    constructor(videoElement, captureCanvas, captureCtx) {
        this.video = videoElement;
        this.captureCanvas = captureCanvas;
        this.captureCtx = captureCtx;
        
        this.isRunning = false;
        this.isRequestPending = false;
        this.intervalMs = 2000; // Matches backend's 2.0s throttle
        this.lastRun = 0;
        
        this.statusEl = null; // We can attach a DOM element here to update status
        this.status = "OFF";
        
        this.lastStableSign = null;
        this.signHistory = [];
        this.consecutiveMatchesRequired = 2; // For temporal stabilization
        this.confidenceThreshold = 0.70;
        
        this.onSignRecognized = null;
    }

    start() {
        if (this.isRunning) return;
        this.isRunning = true;
        this.updateStatus("ACTIVE");
        this.loop = this.loop.bind(this);
        requestAnimationFrame(this.loop);
    }

    stop() {
        this.isRunning = false;
        this.isRequestPending = false;
        this.updateStatus("OFF");
        this.signHistory = [];
        this.lastStableSign = null;
    }

    updateStatus(newStatus, detail = "") {
        this.status = newStatus;
        if (this.statusEl) {
            let color = "var(--text-muted)";
            if (newStatus === "ACTIVE" || newStatus === "ANALYZING") color = "var(--success)";
            else if (newStatus.includes("ERROR")) color = "var(--error)";
            
            this.statusEl.innerHTML = `Ollama Vision: <span style="color: ${color}; font-weight: 600;">● ${newStatus}</span> ${detail ? '('+detail+')' : ''}`;
        }
    }

    async loop(timestamp) {
        if (!this.isRunning) return;
        
        if (timestamp - this.lastRun >= this.intervalMs && !this.isRequestPending && this.video.readyState >= 2) {
            this.lastRun = timestamp;
            await this.analyzeCurrentFrame();
        }
        
        requestAnimationFrame(this.loop);
    }

    async analyzeCurrentFrame() {
        this.isRequestPending = true;
        this.updateStatus("ANALYZING");

        try {
            // Sample a lightweight frame
            this.captureCtx.drawImage(this.video, 0, 0, this.captureCanvas.width, this.captureCanvas.height);
            const base64Image = this.captureCanvas.toDataURL('image/jpeg', 0.6);

            const res = await fetch('/api/vision-assist', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    image: base64Image,
                    context: "Continuous real-time analysis"
                })
            });

            if (!res.ok) {
                this.updateStatus("ERROR", `HTTP ${res.status_code}`);
                return;
            }

            const data = await res.json();
            
            if (data.error) {
                if (data.error.includes("throttled")) {
                    this.updateStatus("ACTIVE", "Waiting for GPU");
                } else {
                    this.updateStatus("ERROR", "Ollama failed");
                    console.warn("Ollama Vision Error:", data.error);
                }
                return;
            }
            
            if (data.result && data.result.sign) {
                this.handleResult(data.result);
                this.updateStatus("ACTIVE", `Sign: ${data.result.sign}`);
            } else {
                this.updateStatus("ACTIVE", "No sign detected");
            }

        } catch (e) {
            this.updateStatus("ERROR", "Connection failed");
            console.warn("Vision Analyzer exception:", e);
        } finally {
            this.isRequestPending = false;
        }
    }

    handleResult(result) {
        if (!result.is_sign || result.confidence < this.confidenceThreshold) {
            this.signHistory = [];
            return;
        }

        const sign = result.sign.toUpperCase();
        this.signHistory.push(sign);
        
        if (this.signHistory.length > this.consecutiveMatchesRequired) {
            this.signHistory.shift();
        }

        // Check if all recent predictions match
        const isStable = this.signHistory.length === this.consecutiveMatchesRequired && 
                         this.signHistory.every(s => s === sign);

        if (isStable) {
            if (this.lastStableSign !== sign) {
                this.lastStableSign = sign;
                
                // Trigger Avatar
                if (this.onSignRecognized) {
                    this.onSignRecognized(sign);
                }
            }
        }
    }
}

window.ContinuousVisionAnalyzer = ContinuousVisionAnalyzer;
