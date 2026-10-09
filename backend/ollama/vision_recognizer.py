import httpx
import json
import base64
import asyncio
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger("SignBridge.VisionRecognizer")

class OllamaVisionRecognizer:
    def __init__(self, host: str, vision_model: str):
        self.host = host
        self.vision_model = vision_model
        self.timeout = 15.0
        self._lock = asyncio.Lock()
        self._vision_test_passed = False

    async def run_vision_test(self) -> bool:
        if self._vision_test_passed:
            return True
            
        import numpy as np
        import cv2
        dummy_img = np.zeros((10, 10, 3), dtype=np.uint8)
        _, buf = cv2.imencode(".jpg", dummy_img)
        b64_str = base64.b64encode(buf).decode("utf-8")
        
        payload = {
            "model": self.vision_model,
            "prompt": "Reply 'YES' in a JSON { \"test\": \"YES\" } if you can see this image.",
            "images": [b64_str],
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 10}
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(f"{self.host}/api/generate", json=payload)
                if res.status_code == 200:
                    self._vision_test_passed = True
                    return True
        except Exception as e:
            logger.error(f"Vision test failed: {e}")
        return False

    async def get_health(self) -> Dict[str, Any]:
        running = False
        vision_available = False
        text_model_name = "llama3.2:1b"
        text_available = False
        
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.host}/api/tags")
                if res.status_code == 200:
                    running = True
                    models = [m.get("name", "") for m in res.json().get("models", [])]
                    vision_available = any(self.vision_model in name for name in models)
                    text_available = any(text_model_name in name for name in models)
        except Exception:
            pass
            
        if running and vision_available and not self._vision_test_passed:
            await self.run_vision_test()

        return {
            "ollama_running": running,
            "text_model": text_model_name,
            "text_model_available": text_available,
            "vision_model": self.vision_model,
            "vision_model_available": vision_available,
            "vision_test": self._vision_test_passed
        }

    async def recognize_sign(
        self,
        image_b64: str,
        landmarks: List[Dict[str, Any]],
        temporal_context: Dict[str, Any],
        candidate_signs: List[str],
        language_candidates: List[str]
    ) -> Dict[str, Any]:
        """
        EMERGENCY STABILIZATION: Extremely simple prompt. No giant JSON payloads.
        """
        if self._lock.locked():
            return {"is_sign": False, "sign": None, "confidence": 0.0, "language": None, "reason": "busy"}

        async with self._lock:
            prompt = (
                "You are a sign-language recognition system.\n"
                "Analyze the hand(s) in the image.\n"
                "Identify the most likely supported sign.\n\n"
                "Pay attention to:\n"
                "- finger configuration\n"
                "- thumb position\n"
                "- palm orientation\n"
                "- hand orientation\n"
                "- number of hands\n"
                "- hand movement if visible\n\n"
                "If the sign cannot be identified confidently, return UNKNOWN.\n\n"
                f"Supported signs: {', '.join(candidate_signs) if candidate_signs else 'NONE'}\n\n"
                "Return JSON only:\n"
                "{\n"
                '  "sign": "...",\n'
                '  "confidence": 0.0,\n'
                '  "language": "ASL"\n'
                "}"
            )

            payload = {
                "model": self.vision_model,
                "prompt": prompt,
                "images": [image_b64],
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 128
                }
            }

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    res = await client.post(f"{self.host}/api/generate", json=payload)
                    if res.status_code == 200:
                        raw = res.json().get("response", "").strip()
                        import re
                        match = re.search(r"\{.*?\}", raw, re.DOTALL)
                        if match:
                            try:
                                parsed = json.loads(match.group(0))
                                sign_val = parsed.get("sign")
                                if sign_val and isinstance(sign_val, str) and sign_val.upper() not in ["NULL", "UNKNOWN", "NONE", "..."]:
                                    upper_sign = sign_val.upper().replace(" ", "_")
                                    if candidate_signs and upper_sign not in candidate_signs:
                                        upper_sign = "UNKNOWN"
                                    
                                    return {
                                        "is_sign": True,
                                        "sign": upper_sign if upper_sign != "UNKNOWN" else None,
                                        "confidence": float(parsed.get("confidence", 0.75)),
                                        "language": parsed.get("language")
                                    }
                            except Exception:
                                pass
            except Exception as e:
                logger.error(f"Simplified Ollama error: {e}")

            return {
                "is_sign": False,
                "sign": None,
                "confidence": 0.0,
                "language": None
            }
