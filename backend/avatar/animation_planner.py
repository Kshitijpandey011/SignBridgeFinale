import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.config import BASE_DIR

class AvatarAnimationPlanner:
    """
    Plans 3D signing sequences from English text.
    Handles tokenization, sign dictionary lookup, and missing sign fallback (fingerspelling).
    """

    def __init__(self):
        self.dict_dir = BASE_DIR / "avatar" / "dictionary"
        self.asl_dict = self._load_json(self.dict_dir / "asl_signs.json")
        self.isl_dict = self._load_json(self.dict_dir / "isl_signs.json")
        self.fingerspelling_dict = self._load_json(self.dict_dir / "fingerspelling.json")

    def _load_json(self, path: Path) -> Dict[str, Any]:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def plan_sequence(self, text: str, mode: str = "ASL") -> Dict[str, Any]:
        mode_upper = mode.upper()
        sign_dict = self.isl_dict if mode_upper == "ISL" else self.asl_dict

        # Sanitize and tokenize
        cleaned = re.sub(r"[^A-Za-z0-9\s_]", " ", text)
        raw_tokens = [t.upper() for t in cleaned.split() if t]

        if not raw_tokens:
            return {
                "text": text,
                "mode": mode_upper,
                "sequence": [],
                "unavailable_words": [],
                "total_duration": 0.0
            }

        # Multi-word sign phrases resolution (e.g. THANK YOU -> THANK_YOU, I LOVE YOU -> I_LOVE_YOU)
        tokens = []
        i = 0
        while i < len(raw_tokens):
            if i + 2 < len(raw_tokens) and f"{raw_tokens[i]}_{raw_tokens[i+1]}_{raw_tokens[i+2]}" in sign_dict:
                tokens.append(f"{raw_tokens[i]}_{raw_tokens[i+1]}_{raw_tokens[i+2]}")
                i += 3
            elif i + 1 < len(raw_tokens) and f"{raw_tokens[i]}_{raw_tokens[i+1]}" in sign_dict:
                tokens.append(f"{raw_tokens[i]}_{raw_tokens[i+1]}")
                i += 2
            else:
                tokens.append(raw_tokens[i])
                i += 1

        sequence = []
        unavailable_words = []
        current_time = 0.0

        for token in tokens:
            if token in sign_dict:
                sign_data = sign_dict[token]
                duration = sign_data.get("duration", 1.0)
                sequence.append({
                    "type": "sign",
                    "word": token,
                    "description": sign_data.get("description", ""),
                    "duration": duration,
                    "start_time": current_time,
                    "keyframes": sign_data.get("keyframes", [])
                })
                current_time += duration + 0.2  # 0.2s transition gap
            else:
                # Sign is unavailable in vocabulary - generate fingerspelling fallback per Section 19!
                unavailable_words.append(token)
                letter_steps = []
                for char in token:
                    if char in self.fingerspelling_dict:
                        f_data = self.fingerspelling_dict[char]
                        dur = f_data.get("duration", 0.5)
                        letter_steps.append({
                            "letter": char,
                            "duration": dur,
                            "right_arm": f_data.get("right_arm", []),
                            "right_hand": f_data.get("right_hand", [])
                        })
                    else:
                        letter_steps.append({
                            "letter": char,
                            "duration": 0.3,
                            "right_arm": [0.6, 0.3, 0.0, 1.4, 0.0, 0.0],
                            "right_hand": [0.5, 0.5, 0.5, 0.5, 0.5]
                        })

                word_duration = sum(s["duration"] for s in letter_steps)
                sequence.append({
                    "type": "fingerspelling",
                    "word": token,
                    "notice": f"Sign animation unavailable for '{token}'; fingerspelling character-by-character.",
                    "duration": word_duration,
                    "start_time": current_time,
                    "letters": letter_steps
                })
                current_time += word_duration + 0.3

        return {
            "text": text,
            "mode": mode_upper,
            "sequence": sequence,
            "unavailable_words": unavailable_words,
            "total_duration": round(current_time, 2)
        }
