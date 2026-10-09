import pyttsx3
import threading
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("SignBridge.TTS")

class LocalTTSEngine:
    """
    Local asynchronous text-to-speech using pyttsx3.
    Executes in a separate thread so it never blocks the server or UI.
    """

    def __init__(self, rate: int = 160, volume: float = 1.0):
        self.rate = rate
        self.volume = volume
        self._lock = threading.Lock()
        self.engine = None
        self.voices = []
        self._init_engine()

    def _init_engine(self):
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", self.rate)
            self.engine.setProperty("volume", self.volume)
            self.voices = self.engine.getProperty("voices")
            logger.info(f"Initialized Local TTS with {len(self.voices)} system voices.")
        except Exception as e:
            logger.error(f"Failed to initialize pyttsx3: {e}")
            self.engine = None

    def get_status(self) -> Dict[str, Any]:
        return {
            "ready": self.engine is not None,
            "voice_count": len(self.voices),
            "voices": [{"id": v.id, "name": v.name} for v in self.voices[:5]] if self.voices else []
        }

    def _speak_worker(self, text: str, voice_hint: Optional[str] = None):
        with self._lock:
            try:
                # Fresh engine per thread to prevent COM initialization collisions on Windows
                eng = pyttsx3.init()
                eng.setProperty("rate", self.rate)
                eng.setProperty("volume", self.volume)
                if voice_hint:
                    for v in eng.getProperty("voices"):
                        if voice_hint.lower() in v.name.lower() or voice_hint.lower() in v.id.lower():
                            eng.setProperty("voice", v.id)
                            break
                eng.say(text)
                eng.runAndWait()
            except Exception as e:
                logger.error(f"TTS playback error: {e}")

    def speak_async(self, text: str, voice_hint: Optional[str] = None):
        """Dispatches speech playback to a background thread."""
        cleaned = text.strip()
        if not cleaned:
            return
        t = threading.Thread(target=self._speak_worker, args=(cleaned, voice_hint), daemon=True)
        t.start()
