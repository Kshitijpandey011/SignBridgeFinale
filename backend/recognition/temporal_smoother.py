import time
from typing import Dict, Any, List, Optional, Tuple
from collections import deque
import logging

logger = logging.getLogger("SignBridge.Smoother")

class TemporalSmoother:
    def __init__(self, window_size: int = 5, confidence_threshold: float = 0.65, debounce_frames: int = 6):
        self.history = deque(maxlen=window_size)
        self.current_sentence: List[str] = []
        self.last_emitted_sign: Optional[str] = None
        self.confidence_threshold = confidence_threshold
        self.debounce_frames = debounce_frames
        
    def update_settings(self, confidence_threshold: Optional[float] = None, debounce_frames: Optional[int] = None):
        if confidence_threshold is not None:
            self.confidence_threshold = confidence_threshold
        if debounce_frames is not None:
            self.debounce_frames = debounce_frames

    def append_manual_word(self, word: str):
        self.current_sentence.append(word.upper())
        return self.get_sentence()

    def delete_last_word(self):
        if self.current_sentence:
            self.current_sentence.pop()
        return self.get_sentence()

    def clear_sentence(self):
        self.current_sentence = []
        self.last_emitted_sign = None
        return ""

    def get_sentence(self):
        return " ".join(self.current_sentence)

    def process_frame_prediction(self, sign: Optional[str], confidence: float) -> Tuple[Optional[str], bool, str]:
        """
        EMERGENCY STABILIZATION: Extremely simple temporal voting.
        - strong confidence (>= 0.85): requires 2 identical signs
        - medium confidence (0.65-0.85): requires 3 identical signs
        - low confidence (< 0.65) or no sign: NO EMISSION
        """
        is_neutral = (not sign) or (sign in ["NONE", "UNKNOWN"])
        
        if is_neutral:
            self.history.clear()
            self.last_emitted_sign = None
            return None, False, self.get_sentence()
            
        self.history.append({"sign": sign, "confidence": confidence})
        
        # Check current sign in history
        count = sum(1 for obs in self.history if obs["sign"] == sign)
        avg_conf = sum(obs["confidence"] for obs in self.history if obs["sign"] == sign) / max(1, count)
        
        emitted = False
        
        # Simple Confirmation Rules
        if avg_conf >= 0.85 and count >= 2:
            if sign != self.last_emitted_sign:
                self.current_sentence.append(sign)
                self.last_emitted_sign = sign
                emitted = True
                self.history.clear()
                return sign, emitted, self.get_sentence()
        elif avg_conf >= 0.65 and count >= 3:
            if sign != self.last_emitted_sign:
                self.current_sentence.append(sign)
                self.last_emitted_sign = sign
                emitted = True
                self.history.clear()
                return sign, emitted, self.get_sentence()
                
        return None, False, self.get_sentence()
