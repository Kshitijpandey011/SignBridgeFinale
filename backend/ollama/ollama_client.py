import httpx
import logging
import subprocess
import shutil
import os
import sys
from typing import Dict, Any, Optional, List
import time
from pathlib import Path

from backend.config import OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_VISION_MODEL, OLLAMA_TIMEOUT_SECONDS

logger = logging.getLogger("SignBridge.Ollama")

class OllamaService:
    """
    Centralized Ollama service layer for translation, sentence refinement, and vision assistance.
    Ensures safe error handling, auto-starts Ollama if installed, and falls back gracefully.
    """

    def __init__(self, host: str = OLLAMA_HOST, model: str = OLLAMA_MODEL, vision_model: str = OLLAMA_VISION_MODEL):
        self.host = host
        self.model = model
        self.vision_model = vision_model
        self.timeout = OLLAMA_TIMEOUT_SECONDS
        self.translation_cache: Dict[str, str] = {}
        self.last_vision_call: float = 0.0
        self.min_vision_interval_seconds: float = 2.0  # Throttle vision model calls
        self._server_proc = None

    def ensure_running(self) -> bool:
        """
        Verifies if Ollama is running. If not, attempts to spawn `ollama serve` in the background.
        """
        try:
            res = httpx.get(f"{self.host}/api/tags", timeout=2.0)
            if res.status_code == 200:
                return True
        except Exception:
            pass

        # Try to locate ollama executable
        ollama_bin = shutil.which("ollama")
        if not ollama_bin:
            default_path = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"
            if default_path.exists():
                ollama_bin = str(default_path)

        if ollama_bin:
            try:
                logger.info(f"Auto-starting Ollama service from {ollama_bin}...")
                flags = 0
                if sys.platform == "win32":
                    flags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
                self._server_proc = subprocess.Popen(
                    [ollama_bin, "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=flags
                )
                # Wait up to 5 seconds for Ollama to initialize
                for _ in range(10):
                    time.sleep(0.5)
                    try:
                        res = httpx.get(f"{self.host}/api/tags", timeout=1.0)
                        if res.status_code == 200:
                            logger.info("Ollama server successfully auto-started.")
                            return True
                    except Exception:
                        pass
            except Exception as e:
                logger.warning(f"Could not auto-start Ollama: {e}")

        return False

    async def check_health(self) -> Dict[str, Any]:
        """
        Pings Ollama server and lists installed models.
        Attempts auto-start if offline.
        """
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.host}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    model_names = [m.get("name", "") for m in data.get("models", [])]
                    has_trans_model = any(self.model in name for name in model_names)
                    has_vision_model = any(self.vision_model in name for name in model_names)
                    return {
                        "running": True,
                        "status": "Connected",
                        "host": self.host,
                        "models": model_names,
                        "translation_model": self.model,
                        "has_translation_model": has_trans_model,
                        "vision_model": self.vision_model,
                        "has_vision_model": has_vision_model,
                        "error": None
                    }
        except Exception:
            # Try to auto-start synchronously
            started = self.ensure_running()
            if started:
                return await self.check_health()

        return {
            "running": False,
            "status": "Offline",
            "host": self.host,
            "models": [],
            "error": "Ollama is not running. Start Ollama to enable AI-assisted features."
        }

    async def translate_text(self, text: str, target_lang_name: str, target_lang_code: str) -> Dict[str, Any]:
        """
        Translates text to the specified Indian language using Ollama (llama3.2:1b).
        Cached in memory to eliminate redundant LLM calls.
        """
        cleaned_text = text.strip()
        if not cleaned_text:
            return {"translated_text": "", "cached": False, "source": "empty"}

        if target_lang_code.lower() == "en" or target_lang_name.lower() == "english":
            return {"translated_text": cleaned_text, "cached": True, "source": "direct"}

        cache_key = f"{target_lang_code.lower()}:{cleaned_text.lower()}"
        if cache_key in self.translation_cache:
            return {
                "translated_text": self.translation_cache[cache_key],
                "cached": True,
                "source": "ollama",
                "model": self.model
            }

        # Ensure Ollama is running before calling
        health = await self.check_health()
        if not health.get("running"):
            return {
                "translated_text": "",
                "error": "Ollama is not running",
                "source": "error"
            }

        system_instruction = (
            f"You are an expert translator from English to {target_lang_name}. "
            f"Translate the following English phrase directly into authentic {target_lang_name} using its native script. "
            "Output ONLY the translated text. Do not provide explanations, transliterations, or markdown."
        )

        payload = {
            "model": self.model,
            "prompt": f"{system_instruction}\n\nEnglish: {cleaned_text}\nTranslation:",
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": 128
            }
        }

        t0 = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.host}/api/generate", json=payload)
                if response.status_code == 200:
                    result = response.json()
                    translated = result.get("response", "").strip()
                    # Clean any accidental quotes or tags
                    translated = translated.strip('"\'`\n\r')
                    latency_ms = round((time.perf_counter() - t0) * 1000)
                    self.translation_cache[cache_key] = translated
                    return {
                        "translated_text": translated,
                        "cached": False,
                        "source": "ollama",
                        "model": self.model,
                        "latency_ms": latency_ms
                    }
                else:
                    return {
                        "translated_text": "",
                        "error": f"Ollama HTTP {response.status_code}",
                        "source": "error"
                    }
        except Exception as e:
            return {
                "translated_text": "",
                "error": f"Ollama connection error: {str(e)}",
                "source": "error"
            }

    async def refine_sentence(self, gloss_text: str) -> Dict[str, Any]:
        """
        Uses Ollama LLM to transform telegraphic sign language glosses (e.g. 'HELLO THANK YOU WATER')
        into a polished, grammatically complete English sentence.
        """
        cleaned = gloss_text.strip()
        if not cleaned:
            return {"refined_text": "", "source": "empty"}

        health = await self.check_health()
        if not health.get("running"):
            return {"refined_text": cleaned, "error": "Ollama offline", "source": "original"}

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You convert telegraphic sign language words into a concise, natural English sentence. Reply with ONLY the sentence in quotes."
                },
                {
                    "role": "user",
                    "content": f"Words: {cleaned}"
                }
            ],
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 48
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(f"{self.host}/api/chat", json=payload)
                if res.status_code == 200:
                    raw_content = res.json().get("message", {}).get("content", "").strip()
                    # Extract text inside quotes if present
                    if '"' in raw_content:
                        parts = raw_content.split('"')
                        if len(parts) >= 2 and parts[1].strip():
                            refined = parts[1].strip()
                        else:
                            refined = raw_content.strip('"\'`\n\r ')
                    else:
                        refined = raw_content.strip('"\'`\n\r ')
                    return {"refined_text": refined, "source": "ollama", "model": self.model}
        except Exception as e:
            logger.error(f"Refinement error: {e}")

        return {"refined_text": cleaned, "source": "fallback"}

    async def validate_sign_with_vision(self, base64_image: str, mode: str, candidate_sign: Optional[str] = None) -> Dict[str, Any]:
        """
        Uses Ollama Vision model (qwen2.5vl:3b) to validate ambiguous or medium-confidence signs.
        Guarantees strict JSON structured output and enforces a single concurrent call lock.
        """
        if not hasattr(self, "_vision_lock"):
            self._vision_lock = asyncio.Lock()

        if self._vision_lock.locked():
            return {"sign": None, "confidence": 0.0, "reason": "busy"}

        async with self._vision_lock:
            prompt = (
                f"You are an expert Sign Language computer vision analyzer. "
                "Analyze the CURRENT image independently. Determine whether a recognizable sign is actually being performed. "
                "Do not assume the previous prediction is correct. Do not use the previous sign as evidence. "
                "If the evidence is insufficient or the hand is visible but does not confidently match a supported sign, return UNKNOWN. "
                "Respond ONLY with a raw JSON object and nothing else:\n"
                "{\n"
                '  "is_sign": true,\n'
                '  "sign": "THANK_YOU",\n'
                '  "confidence": 0.91,\n'
                '  "language": "ASL",\n'
                '  "hand_count": 1\n'
                "}\n"
                'For uncertain frames return: {"is_sign": false, "sign": "UNKNOWN", "confidence": 0.0, "language": null, "hand_count": 1}'
            )

            payload = {
                "model": self.vision_model,
                "prompt": prompt,
                "images": [base64_image],
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 48
                }
            }

            try:
                async with httpx.AsyncClient(timeout=12.0) as client:
                    res = await client.post(f"{self.host}/api/generate", json=payload)
                    if res.status_code == 200:
                        raw = res.json().get("response", "").strip()
                        # Extract JSON object using regex
                        import re
                        match = re.search(r"\{.*?\}", raw, re.DOTALL)
                        if match:
                            try:
                                parsed = json.loads(match.group(0))
                                sign_val = parsed.get("sign")
                                if sign_val and isinstance(sign_val, str) and sign_val.upper() != "NULL":
                                    return {
                                        "sign": sign_val.upper().replace(" ", "_"),
                                        "confidence": float(parsed.get("confidence", 0.75)),
                                        "language": mode,
                                        "hand_count": int(parsed.get("hand_count", 1))
                                    }
                            except Exception:
                                pass
            except Exception as e:
                logger.debug(f"Vision validation request error: {e}")

            return {"sign": None, "confidence": 0.0}

    async def convert_english_to_sign_gloss(self, text: str, mode: str, allowed_signs: List[str]) -> List[str]:
        """
        Converts English text into a sign sequence constrained strictly to known vocabulary.
        Prevents Ollama from hallucinating unknown signs.
        """
        cleaned = text.strip()
        if not cleaned:
            return []

        allowed_str = ", ".join(allowed_signs[:50])
        prompt = (
            f"Convert this English sentence into a sequence of sign words in {mode}. "
            f"You may ONLY choose words from this allowed vocabulary list: [{allowed_str}]. "
            "Output ONLY the comma-separated sign words. Words not in list should be omitted.\n\n"
            f"Sentence: {cleaned}\nSign sequence:"
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 32}
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(f"{self.host}/api/generate", json=payload)
                if res.status_code == 200:
                    raw = res.json().get("response", "").strip()
                    tokens = [t.strip().upper().replace(" ", "_") for t in raw.split(",") if t.strip()]
                    valid_tokens = [t for t in tokens if t in allowed_signs]
                    if valid_tokens:
                        return valid_tokens
        except Exception:
            pass

        return [w.upper() for w in cleaned.split() if w.upper() in allowed_signs]

    async def analyze_vision_frame(self, base64_image: str, context: str = "") -> Dict[str, Any]:
        """
        Sends an image to Ollama Vision Model (e.g. qwen2.5vl:3b) for continuous sign interpretation.
        Throttled to avoid overwhelming the GPU.
        """
        now = time.time()
        if now - self.last_vision_call < self.min_vision_interval_seconds:
            return {
                "error": "Vision call throttled to conserve GPU memory. Please wait a moment.",
                "sign": None,
                "confidence": 0.0
            }

        self.last_vision_call = now

        prompt = (
            "Analyze this sign language video frame independently. Identify the exact sign being performed. "
            "Carefully analyze not just the hands, but also the FACE (expressions, mouth), "
            "SHOULDERS, and CHEST (posture, shifting) to capture the full grammatical context of the sign. "
            "Do not choose a sign merely because it is common or because it was predicted previously. "
            "If the current evidence is insufficient or no sign is visible, return UNKNOWN. "
            "Valid Candidates: [HELLO, THANK_YOU, YES, NO, PLEASE, SORRY, HELP, I_LOVE_YOU, GOOD, BAD, WATER, PEACE]. "
            f"Context: {context}. "
            "Reply STRICTLY with JSON matching this schema: "
            "{\"language\": \"ASL\", \"language_confidence\": 0.95, \"sign\": \"UNKNOWN\", \"sign_confidence\": 0.90, \"hand\": \"right\", \"is_sign\": false}"
        )

        payload = {
            "model": self.vision_model,
            "prompt": prompt,
            "images": [base64_image],
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 128,
                "num_ctx": 8192
            }
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(f"{self.host}/api/generate", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    response_text = data.get("response", "").strip()
                    logger.info(f"[VISION DEBUG] RAW OLLAMA: {response_text}")
                    import json
                    try:
                        # Find the json portion
                        import re
                        match = re.search(r'\{.*\}', response_text, re.DOTALL)
                        if match:
                            parsed = json.loads(match.group(0))
                            logger.info(f"[VISION DEBUG] PARSED: {parsed}")
                            return {"result": parsed, "error": None}
                        else:
                            # Try to parse entire thing
                            parsed = json.loads(response_text)
                            logger.info(f"[VISION DEBUG] PARSED: {parsed}")
                            return {"result": parsed, "error": None}
                    except json.JSONDecodeError:
                        logger.warning(f"[VISION DEBUG] JSONDecodeError on: {response_text}")
                        return {"error": "Invalid JSON from Ollama", "result": None}
                
                logger.error(f"Ollama Vision API returned {res.status_code}: {res.text}")
                return {"error": f"Ollama Vision error: HTTP {res.status_code}", "result": None}
        except Exception as e:
            return {"error": f"Ollama Vision failed: {str(e)}", "result": None}
