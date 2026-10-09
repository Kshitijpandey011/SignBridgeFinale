import asyncio
import time
import logging
import base64
from typing import Dict, Any, Optional, List
import cv2

logger = logging.getLogger("SignBridge.HybridRecognizer")

class HybridSignRecognizer:
    """
    EMERGENCY STABILIZATION: Simplified Recognition Worker
    - ONLY uses Ollama Vision (local classifier is bypassed completely).
    - EXACTLY 1 request per second max.
    - No request piling (latest frame buffer).
    - No large JSON payloads (landmarks removed for now).
    """

    def __init__(self, ollama_service, debug: bool = False):
        self.ollama = ollama_service
        self.min_vision_interval = 1.0  # STRICTLY 1 FPS
        self.debug = debug

        # Worker state
        self._worker_task = None
        self._latest_frame_data = None
        self._vision_in_flight = False
        self._last_vision_time = 0.0
        self._latest_vision_result: Optional[Dict[str, Any]] = None

        self._start_worker()

    def _start_worker(self):
        try:
            loop = asyncio.get_running_loop()
            self._worker_task = loop.create_task(self._vision_worker_loop())
        except RuntimeError:
            pass 

    async def _vision_worker_loop(self):
        logger.info("Simplified 1-FPS Vision Worker started.")
        while True:
            if self._latest_frame_data is None:
                await asyncio.sleep(0.05)
                continue
                
            now = time.perf_counter()
            if (now - self._last_vision_time) < self.min_vision_interval:
                await asyncio.sleep(0.05)
                continue
                
            # Pop latest frame
            req_data = self._latest_frame_data
            self._latest_frame_data = None
            
            frame_bgr = req_data['frame']
            landmarks_data = req_data['landmarks']
            
            self._vision_in_flight = True
            self._last_vision_time = time.perf_counter()
            
            try:
                # 1. Simple Crop (25% padding)
                h, w, _ = frame_bgr.shape
                x_min, y_min = w, h
                x_max, y_max = 0, 0
                
                if landmarks_data:
                    for hand in landmarks_data:
                        for pt in hand.get("points", []):
                            x, y = int(pt["x"] * w), int(pt["y"] * h)
                            x_min = min(x_min, x)
                            y_min = min(y_min, y)
                            x_max = max(x_max, x)
                            y_max = max(y_max, y)
                            
                    pad_x = int((x_max - x_min) * 0.25)
                    pad_y = int((y_max - y_min) * 0.25)
                    x_min = max(0, x_min - pad_x)
                    y_min = max(0, y_min - pad_y)
                    x_max = min(w, x_max + pad_x)
                    y_max = min(h, y_max + pad_y)
                    
                    crop = frame_bgr[y_min:y_max, x_min:x_max]
                else:
                    crop = frame_bgr

                if crop.size == 0:
                    crop = frame_bgr

                # Simple scale (target 512 max dimension)
                max_dim = max(crop.shape[0], crop.shape[1])
                scale = 512.0 / max(1, max_dim)
                if scale < 1.0:
                    new_w, new_h = int(crop.shape[1] * scale), int(crop.shape[0] * scale)
                    crop = cv2.resize(crop, (new_w, new_h), interpolation=cv2.INTER_AREA)

                _, buf = cv2.imencode(".jpg", crop, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                b64_str = base64.b64encode(buf).decode("utf-8")

                from backend.recognition.sign_vocabulary import get_sign_list
                candidates = get_sign_list("ASL") + get_sign_list("ISL")
                languages = ["ASL", "ISL"]
                
                # TEMPORARILY: Do NOT send landmarks to Ollama (simplifying the prompt)
                res = await self.ollama.recognize_sign(
                    image_b64=b64_str,
                    landmarks=[], 
                    temporal_context={},
                    candidate_signs=list(set(candidates)),
                    language_candidates=languages
                )
                
                if res:
                    res["timestamp"] = time.perf_counter()
                    self._latest_vision_result = res
                    
            except Exception as e:
                logger.error(f"Simplified worker error: {e}")
            finally:
                self._vision_in_flight = False

    def evaluate_sign(self,
                      mode: str,
                      local_sign: Optional[str],
                      local_conf: float,
                      local_probs: Dict[str, float],
                      frame_bgr,
                      has_hands: bool,
                      landmarks_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Emergency Stabilization: 
        Ignores local classifier entirely. Only returns the latest Ollama result.
        """
        now = time.perf_counter()
        
        # 1. Update latest frame buffer
        if has_hands and frame_bgr is not None:
            self._latest_frame_data = {
                'frame': frame_bgr.copy(),
                'landmarks': landmarks_data
            }
            if self._worker_task is None or self._worker_task.done():
                self._start_worker()
            
        # 2. Return the most recent Ollama vision result if it exists (within 2 seconds)
        recent_ollama = None
        if self._latest_vision_result:
            if (now - self._latest_vision_result.get("timestamp", 0)) <= 2.0:
                recent_ollama = self._latest_vision_result

        ollama_sign = recent_ollama.get("sign") if recent_ollama else None
        ollama_conf = recent_ollama.get("confidence", 0.0) if recent_ollama else 0.0
        ollama_lang = recent_ollama.get("language") if recent_ollama else None

        final_sign = "UNKNOWN"
        final_conf = 0.0
        rec_source = "none"

        if not has_hands:
            final_sign = "NONE"
            final_conf = 1.0
            rec_source = "no_hands"
        elif ollama_sign and ollama_sign != "UNKNOWN":
            final_sign = ollama_sign
            final_conf = ollama_conf
            rec_source = "ollama_primary"
        else:
            final_sign = "UNKNOWN"
            final_conf = 0.0
            rec_source = "uncertain"

        out_mode = ollama_lang if ollama_lang else mode
        
        # We indicate exactly what the status of the worker is, for the UI
        ollama_status = "OLLAMA ANALYZING" if self._vision_in_flight else "OLLAMA READY"

        return {
            "mode": out_mode,
            "local_sign": None,  # Disabled
            "local_confidence": 0.0,
            "ollama_sign": ollama_sign,
            "ollama_confidence": round(ollama_conf, 3),
            "final_sign": final_sign,
            "final_confidence": round(final_conf, 3),
            "recognition_source": rec_source,
            "ollama_status": ollama_status,
            "top_probabilities": {}
        }
