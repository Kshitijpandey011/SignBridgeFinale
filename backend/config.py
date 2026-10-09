import os
from pathlib import Path
from dotenv import load_dotenv

import sys

# Base directory of the repository
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
dotenv_path = BASE_DIR / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)

# Server settings
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

# Camera settings
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
RECOGNITION_FPS = int(os.getenv("RECOGNITION_FPS", "24"))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.65"))
TEMPORAL_SMOOTHING_WINDOW = int(os.getenv("TEMPORAL_SMOOTHING_WINDOW", "8"))
DEBOUNCE_FRAMES = int(os.getenv("DEBOUNCE_FRAMES", "6"))

# AI Models paths
ASL_MODEL_PATH = BASE_DIR / os.getenv("ASL_MODEL_PATH", "models/asl/asl_classifier.joblib")
ISL_MODEL_PATH = BASE_DIR / os.getenv("ISL_MODEL_PATH", "models/isl/isl_classifier.joblib")

# Ollama settings
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
OLLAMA_VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "qwen2.5vl:3b")
OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "10.0"))

# TTS settings
TTS_RATE = int(os.getenv("TTS_RATE", "160"))
TTS_VOLUME = float(os.getenv("TTS_VOLUME", "1.0"))

# Supported Indian Languages mapping for translation
SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "native": "English", "speech_code": "en-US"},
    "hi": {"name": "Hindi", "native": "हिन्दी", "speech_code": "hi-IN"},
    "ta": {"name": "Tamil", "native": "தமிழ்", "speech_code": "ta-IN"},
    "te": {"name": "Telugu", "native": "తెలుగు", "speech_code": "te-IN"},
    "kn": {"name": "Kannada", "native": "ಕನ್ನಡ", "speech_code": "kn-IN"},
    "ml": {"name": "Malayalam", "native": "മലയാളം", "speech_code": "ml-IN"},
    "mr": {"name": "Marathi", "native": "मराठी", "speech_code": "mr-IN"},
    "bn": {"name": "Bengali", "native": "বাংলা", "speech_code": "bn-IN"},
    "gu": {"name": "Gujarati", "native": "ગુજરાતી", "speech_code": "gu-IN"},
    "pa": {"name": "Punjabi", "native": "ਪੰਜਾਬੀ", "speech_code": "pa-IN"},
    "ur": {"name": "Urdu", "native": "اردو", "speech_code": "ur-PK"},
    "or": {"name": "Odia", "native": "ଓଡ଼ିଆ", "speech_code": "or-IN"},
    "as": {"name": "Assamese", "native": "অসমীয়া", "speech_code": "as-IN"}
}
