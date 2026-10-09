# SIGNBRIDGE — Unified ASL + ISL Sign Recognition, Translation & 3D Signing Assistant

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.14-00A389.svg)](https://developers.google.com/mediapipe)
[![Three.js](https://img.shields.io/badge/Three.js-r128-black.svg)](https://threejs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 1. Project Overview

**SIGNBRIDGE** is a unified, offline-first single-window desktop/web application engineered for real-time two-way communication between the Deaf/Hard-of-Hearing community and hearing individuals.

The system combines three major capabilities directly within **ONE UNIFIED SCREEN**:
1. **Live Camera Sign Recognition**: Real-time webcam tracking using OpenCV and MediaPipe landmark detection with separate, dedicated classifiers for **ASL** (American Sign Language) and **ISL** (Indian Sign Language).
2. **Indian Language Translation & Speech**: English sign sentence formation with neural translation into 12 Indian languages powered by local **Ollama** (`llama3.2:1b`) and zero-latency offline vocabulary fallbacks.
3. **Interactive 3D Signing Avatar**: Real-time WebGL skeletal humanoid that articulates sign sequences from user-entered text, equipped with graceful character-by-character fingerspelling for missing vocabulary.

Designed and optimized specifically for laptops with limited hardware (e.g., **NVIDIA 6 GB VRAM GPUs**), SIGNBRIDGE executes inference in sub-25ms with practically zero VRAM bloat.

---

## 2. Key Features

- **Single-Window Dashboard**: No navigation across disparate tabs or windows. Camera, English sentences, Indian translations, and 3D avatar operate concurrently on one screen.
- **ASL + ISL Separation**: Strictly distinguishes ASL and ISL as separate linguistic models and gesture grammars.
- **No Fake Predictions**: Explicitly validates model presence. If a model file is missing or uncalibrated, it reports `Model not trained/available` rather than hallucinating predictions.
- **Temporal Prediction Smoothing**: Sliding window majority voting (8 frames) combined with state-transition debouncing to eliminate duplicate sign spam (e.g. `HELLO HELLO HELLO`).
- **12 Indian Languages Supported**:
  - Hindi (हिन्दी)
  - Tamil (தமிழ்)
  - Telugu (తెలుగు)
  - Kannada (ಕನ್ನಡ)
  - Malayalam (മലയാളം)
  - Marathi (मराठी)
  - Bengali (বাংলা)
  - Gujarati (ગુજરાતી)
  - Punjabi (ਪੰਜਾਬੀ)
  - Urdu (اردو)
  - Odia (ଓଡ଼ିଆ)
  - Assamese (অসমীয়া)
  - English
- **Offline-First & Ollama Integration**: Runs completely offline using fast vocabulary lookup tables; automatically utilizes local Ollama neural LLM for complex sentences when Ollama is active.
- **Dual Text-to-Speech**: Instant native browser speech synthesis plus asynchronous background `pyttsx3` desktop audio.
- **Lightweight 3D WebGL Avatar**: 60 FPS Three.js articulated avatar with 5-finger articulation, speed control (0.75x–1.5x), camera orbit controls, and fingerspelling fallback.

---

## 3. Architecture

```
SIGNBRIDGE/
│
├── backend/
│   ├── config.py                 # Centralized configuration & environment loader
│   ├── main.py                   # FastAPI application & static server
│   ├── api/
│   │   └── routes.py             # REST endpoints & WebSocket live stream
│   ├── recognition/
│   │   ├── feature_extractor.py  # 150-dim scale/position invariant hand feature extractor
│   │   ├── landmark_detector.py  # MediaPipe Hands 21-landmark tracking wrapper
│   │   ├── sign_classifier.py    # ASL/ISL model lifecycle manager
│   │   ├── temporal_smoother.py  # Majority voting & cooldown debouncing
│   │   └── sign_vocabulary.py   # Vocabulary metadata & grammar specs
│   ├── translation/
│   │   ├── translator.py         # Neural + offline translation orchestrator
│   │   └── offline_dictionary.py # 12-language lookup table
│   ├── tts/
│   │   └── speech_engine.py      # Non-blocking pyttsx3 worker thread
│   ├── ollama/
│   │   └── ollama_client.py      # Ollama HTTP client (translation & vision assist)
│   └── avatar/
│       └── animation_planner.py  # Text tokenization & keyframe sequence planner
│
├── frontend/
│   ├── index.html                # Unified single-screen dashboard
│   ├── css/
│   │   ├── styles.css            # Dark glassmorphic design system
│   │   └── dashboard.css         # Single-screen responsive grid
│   └── js/
│       ├── three.min.js          # Local Three.js r128 library (100% offline)
│       ├── app.js                # Main frontend controller
│       ├── camera.js             # Webcam capture & canvas landmark renderer
│       ├── avatar_engine.js      # Three.js 3D WebGL avatar player & orbit controls
│       ├── translation.js        # Debounced translation controller
│       ├── tts.js                # Dual speech synthesis controller
│       └── status_manager.js     # System health polling
│
├── models/
│   ├── asl/                      # ASL model bundle (joblib) & config.json
│   └── isl/                      # ISL model bundle (joblib) & config.json
│
├── avatar/
│   └── dictionary/
│       ├── asl_signs.json        # Keyframe rotations for ASL signs
│       ├── isl_signs.json        # Keyframe rotations for ISL signs
│       └── fingerspelling.json   # A-Z individual letter hand shapes
│
├── data/
│   ├── asl/                      # User-recorded custom training samples
│   └── isl/
│
├── scripts/
│   ├── collect_data.py           # Webcam recording tool for custom signs
│   ├── train_models.py           # Feature training pipeline & exporter
│   └── verify_system.py          # Subsystem benchmark & latency checker
│
├── tests/                        # 16 Pytest unit & integration tests
├── .env.example / .env
├── requirements.txt
├── setup.bat
├── run.bat
└── run.py
```

---

## 4. Hardware Requirements

- **GPU**: NVIDIA GPU with 6 GB VRAM (e.g., RTX 3050/3060/4050 Laptop).
- **RAM**: 8 GB minimum (16 GB recommended).
- **Webcam**: Standard 720p or 1080p USB or integrated laptop webcam.
- **CPU**: Intel Core i5/i7 (10th gen+) or AMD Ryzen 5/7.
- **VRAM Footprint**:
  - Sign Recognition & CV: ~150 MB VRAM / RAM
  - 3D Avatar WebGL: ~45 MB VRAM
  - Ollama (`llama3.2:1b`): ~1.3 GB VRAM during active translation
  - Total Peak VRAM: **< 1.8 GB**, safely beneath the 6 GB ceiling.

---

## 5. Software Requirements

- **Operating System**: Windows 10 or Windows 11 (64-bit).
- **Python**: 3.10, 3.11, or 3.12 (Python 3.12 verified).
- **Ollama**: Installed locally from [ollama.com](https://ollama.com).
- **Web Browser**: Microsoft Edge, Google Chrome, Brave, or Firefox.

---

## 6. Installation

1. Clone or extract the repository:
   ```bash
   cd "c:\Users\kshit\OneDrive\Documents\APP Proja - Copy"
   ```

2. Run the automated setup script:
   ```bash
   setup.bat
   ```
   Or install manually via pip:
   ```bash
   python -m pip install -r requirements.txt
   ```

---

## 7. Ollama Setup

1. Verify that Ollama is installed on your Windows machine:
   ```bash
   ollama --version
   ```
2. Pull the recommended lightweight translation model:
   ```bash
   ollama pull llama3.2:1b
   ```
3. Optional: Pull the vision model for ambiguous frame inspection:
   ```bash
   ollama pull qwen2.5vl:3b
   ```
4. Start Ollama in a separate PowerShell window:
   ```bash
   ollama serve
   ```
   *Note: If Ollama is not running, SIGNBRIDGE automatically runs in offline mode using its built-in dictionary.*

---

## 8. Model Setup

To train or retrain the initial ASL and ISL model bundles:
```bash
python scripts/train_models.py
```
This trains calibrated Random Forest classifiers with 150-dimension invariant geometric feature vectors and exports:
- `models/asl/asl_classifier.joblib`
- `models/isl/isl_classifier.joblib`

---

## 9. Running the Application

### Option A: One-Command Batch Launcher
Double-click `run.bat` or run:
```cmd
run.bat
```

### Option B: Python Launcher
```bash
python run.py
```

The application will verify environment health, check Ollama, start the FastAPI server at `http://127.0.0.1:8000`, and automatically launch your browser dashboard.

---

## 10. ASL Recognition Setup

- Switch mode to **ASL** using the top header pill.
- Initial vocabulary (12 signs):
  `HELLO`, `THANK_YOU`, `YES`, `NO`, `PLEASE`, `SORRY`, `HELP`, `I_LOVE_YOU`, `GOOD`, `BAD`, `WATER`, `PEACE`
- Click `📖 Vocabulary` in the camera toolbar to inspect sign descriptions and test them directly on the 3D avatar.

---

## 11. ISL Recognition Setup

- Switch mode to **ISL** using the top header pill.
- Initial vocabulary (13 signs):
  `NAMASTE`, `THANK_YOU`, `YES`, `NO`, `PLEASE`, `SORRY`, `HELP`, `WATER`, `FOOD`, `HOME`, `SCHOOL`, `GOOD`, `BAD`
- Supports two-handed relational gestures (e.g., Namaste, Home roof peak, Clapping School gesture).

---

## 12. Translation Setup

- The dashboard automatically translates detected or typed English sentences.
- Select your target language from the dropdown menu (e.g. Hindi, Tamil, Telugu, Kannada, Marathi, etc.).
- When Ollama is running, high-quality neural translation is executed and cached.
- When Ollama is offline, the system translates using the fast dictionary fallback.

---

## 13. TTS Setup

- **Speak English**: Reads recognized English sentences out loud.
- **Speak Translation**: Reads target Indian language output out loud using native browser speech synthesis or backend `pyttsx3`.
- Speech execution runs asynchronously in the background and never blocks UI responsiveness.

---

## 14. 3D Avatar Setup

- Powered by Three.js WebGL canvas in the bottom panel.
- Articulated upper body with realistic shoulder, elbow, wrist, and individual finger joints.
- **Controls**:
  - Type arbitrary text and click `🤟 MAKE AVATAR SIGN` (or press `Enter`).
  - `[ ▶ Play ]`, `[ ⏸ Pause ]`, `[ ⏹ Stop ]`.
  - Speed selector: `0.75x`, `1.0x`, `1.25x`, `1.5x`.
  - Orbit Camera: Click and drag on the 3D canvas to rotate; scroll mouse wheel to zoom; click `⟲ Reset View` to reset perspective.

---

## 15. Adding New Signs to Vocabulary

1. Open `backend/recognition/sign_vocabulary.py`.
2. Add the sign definition under `ASL_VOCABULARY` or `ISL_VOCABULARY`:
   ```python
   "BOOK": {
       "type": "static",
       "hands": 2,
       "description": "Both palms open side by side like opening a book"
   }
   ```
3. Add the corresponding 3D avatar keyframes in `avatar/dictionary/asl_signs.json` or `avatar/dictionary/isl_signs.json`.

---

## 16. Training Custom Signs with Your Webcam

To record real samples using your own webcam:
```bash
python scripts/collect_data.py ASL HELLO 50
```
- Press `SPACE` to toggle recording.
- Saves 50 landmark feature arrays into `data/asl/HELLO/`.
- Re-run `python scripts/train_models.py` to retrain the classifier with your recorded samples.

---

## 17. Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `Camera: Offline` | Camera permission denied or device in use | Ensure other apps (Teams, Zoom, WhatsApp) are closed; click `Start Camera`. |
| `Ollama: Offline` | Ollama process not running | Run `ollama serve` in a separate PowerShell window. |
| `Model not trained` | Model `.joblib` file missing | Run `python scripts/train_models.py`. |
| `Duplicate sign spam` | Cooldown threshold too low | Adjust confidence slider up to 70% or 75%. |
| `Avatar not moving` | Text input was empty | Enter words or click any of the preset sign pills (e.g. `HELLO`). |

---

## 18. Performance Optimization

- **Inference FPS Throttling**: Camera captures at 30 FPS, while inference is throttled to 15 FPS to conserve laptop battery and CPU/GPU cycles.
- **Sub-25ms Latency**: MediaPipe hands feature extraction + Random Forest inference executes in ~21 ms per frame.
- **Translation Caching**: In-memory LRU cache prevents redundant model invocations.
- **Local Three.js**: Bundled locally so no CDN network requests block page rendering.

---

## 19. Known Limitations

- Dynamic trajectory-based signs with large circular body movements (e.g. multi-second complex stories) are approximated with keyframe segments; full dynamic LSTM/GRU sequence modeling can be added for multi-stage continuous signing.
- Face landmark affect (facial expressions / eyebrow raises) is currently not incorporated into the classifier features.

---

## 20. Future Improvements

- Add ISL two-handed fingerspelling character animations.
- Integrate MediaPipe Holistic for facial expression affect and full torso pose angles.
- Support user-recorded video file uploads for batch offline recognition.
- Provide custom GLTF/GLB avatar skin model customization.

---

## 21. Tests & Verification

Run the complete test suite:
```bash
python -m pytest tests/
```
Output:
```
======================= 16 passed in 18.68s =======================
```

Run system verification and latency benchmarks:
```bash
python scripts/verify_system.py
```
Output:
```
[1/6] Checking ASL and ISL Models...
  [OK] ASL Model Ready: 12 signs
  [OK] ISL Model Ready: 13 signs
[2/6] Benchmarking Feature Extraction & Classifier Latency...
  [OK] Average Inference Latency: 21.75 ms per frame (~46 FPS potential)
[3/6] Checking Webcam Index 0...
  [OK] Webcam connected and captured frame: 1280x720
[4/6] Checking Local Ollama AI at http://localhost:11434...
  [OK] Ollama server online. Detected models: llama3.2:1b, qwen2.5vl:3b
[5/6] Checking Translation Module...
  [OK] Supported Indian Languages (13): en, hi, ta, te, kn, ml, mr, bn, gu, pa, ur, or, as
[6/6] Checking 3D Avatar Keyframe Dictionaries & Planner...
  [OK] ASL Keyframe Signs: 11
  [OK] ISL Keyframe Signs: 5
  [OK] Fingerspelling Alphabet: 26 letters
  [OK] Missing sign fallback (fingerspelling) verified.
```
