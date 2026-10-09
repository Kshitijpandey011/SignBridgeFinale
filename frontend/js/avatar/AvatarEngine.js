class AvatarEngine {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;

        // Interaction
        this.isMouseDown = false;
        this.mouseX = 0;
        this.mouseY = 0;
        this.camTargetAngleX = 0;
        this.camTargetAngleY = 0.05;
        this.camDistance = 2.35;

        this.statusEl = document.getElementById('avatar-sign-now');
        this.noticeEl = document.getElementById('missing-sign-notice');
        
        // Modules
        this.skeleton = null;
        this.animator = null;
    }

    init() {
        if (!this.canvas) return;
        const width = this.canvas.clientWidth || 320;
        const height = this.canvas.clientHeight || 220;

        // Scene
        this.scene = new THREE.Scene();

        // Camera
        this.camera = new THREE.PerspectiveCamera(38, width / height, 0.1, 50);
        this.camera.position.set(0, 0.42, this.camDistance);

        // Renderer
        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            antialias: true,
            alpha: true,
            powerPreference: "high-performance"
        });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.75);
        this.scene.add(ambientLight);

        const keyLight = new THREE.DirectionalLight(0x38bdf8, 1.3);
        keyLight.position.set(1.8, 2.5, 3.0);
        this.scene.add(keyLight);

        const fillLight = new THREE.DirectionalLight(0x818cf8, 0.6);
        fillLight.position.set(-1.8, 1.5, 2.0);
        this.scene.add(fillLight);

        const rimLight = new THREE.DirectionalLight(0x06b6d4, 0.9);
        rimLight.position.set(0, 2.0, -2.5);
        this.scene.add(rimLight);

        // Modules
        this.skeleton = new AvatarSkeleton(this.scene);
        this.animator = new AvatarAnimationController(this.skeleton);
        this.animator.onStatusChange = (msg) => {
            if (this.statusEl) this.statusEl.textContent = msg;
        };

        // Reset to idle
        this.animator.resetToIdle();

        this.setupInteraction();

        // Start render loop
        this.animate = this.animate.bind(this);
        requestAnimationFrame(this.animate);
    }

    get isPaused() {
        return this.animator ? this.animator.isPaused : false;
    }

    get playbackSpeed() {
        return this.animator ? this.animator.playbackSpeed : 1.0;
    }

    set playbackSpeed(val) {
        if (this.animator) this.animator.playbackSpeed = val;
    }

    playSequence(plan) {
        if (plan && plan.unavailable_words && plan.unavailable_words.length > 0) {
            if (this.noticeEl) {
                this.noticeEl.textContent = `Sign animation unavailable for: "${plan.unavailable_words.join(', ')}". Fingerspelling character-by-character.`;
                this.noticeEl.className = 'notice-banner show';
            }
        } else {
            if (this.noticeEl) this.noticeEl.className = 'notice-banner';
        }
        
        if (this.animator) {
            this.animator.playSequence(plan);
        }
    }

    pause() {
        if (this.animator) this.animator.pause();
    }

    resume() {
        if (this.animator) this.animator.resume();
    }

    stop() {
        if (this.animator) this.animator.stop();
        if (this.noticeEl) this.noticeEl.className = 'notice-banner';
    }

    setupInteraction() {
        this.canvas.addEventListener('mousedown', (e) => {
            this.isMouseDown = true;
            this.mouseX = e.clientX;
            this.mouseY = e.clientY;
        });

        window.addEventListener('mouseup', () => {
            this.isMouseDown = false;
        });

        window.addEventListener('mousemove', (e) => {
            if (!this.isMouseDown) return;
            const dx = e.clientX - this.mouseX;
            const dy = e.clientY - this.mouseY;
            this.mouseX = e.clientX;
            this.mouseY = e.clientY;

            this.camTargetAngleX += dx * 0.01;
            this.camTargetAngleY = Math.max(-0.35, Math.min(0.65, this.camTargetAngleY + dy * 0.01));
        });

        this.canvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            this.camDistance = Math.max(1.5, Math.min(3.6, this.camDistance + e.deltaY * 0.002));
        });

        const resetBtn = document.getElementById('avatar-reset-cam-btn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.camTargetAngleX = 0;
                this.camTargetAngleY = 0.05;
                this.camDistance = 2.35;
            });
        }
    }

    animate(now) {
        requestAnimationFrame(this.animate);

        // Camera orbit
        const x = Math.sin(this.camTargetAngleX) * this.camDistance;
        const z = Math.cos(this.camTargetAngleX) * this.camDistance;
        const y = 0.42 + this.camTargetAngleY;

        this.camera.position.x += (x - this.camera.position.x) * 0.12;
        this.camera.position.y += (y - this.camera.position.y) * 0.12;
        this.camera.position.z += (z - this.camera.position.z) * 0.12;
        this.camera.lookAt(0, 0.42, 0);

        // Update animation logic
        if (this.animator) {
            this.animator.update(now);
        }

        // Render frame
        if (this.renderer && this.scene && this.camera) {
            this.renderer.render(this.scene, this.camera);
        }
    }
}

window.AvatarEngine = AvatarEngine;
