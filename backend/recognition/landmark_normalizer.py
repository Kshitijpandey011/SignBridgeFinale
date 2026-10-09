import numpy as np
import cv2
from typing import Dict, Any, List, Optional
from collections import deque
import time

class LandmarkNormalizer:
    """
    Constructs a geometrically accurate, stable, scale-invariant, orientation-aware,
    and temporally consistent representation of hands.
    """
    def __init__(self, temporal_window_size: int = 5):
        self.temporal_window_size = temporal_window_size
        self.history = deque(maxlen=temporal_window_size)
    
    def _calculate_palm_center(self, coords: np.ndarray) -> np.ndarray:
        # Average of Wrist(0), IndexMCP(5), MiddleMCP(9), RingMCP(13), PinkyMCP(17)
        return np.mean(coords[[0, 5, 9, 13, 17]], axis=0)

    def _calculate_scale(self, coords: np.ndarray) -> float:
        # Distance from Wrist(0) to MiddleMCP(9)
        scale = np.linalg.norm(coords[9] - coords[0])
        return max(scale, 1e-6)

    def _calculate_orientation(self, coords: np.ndarray) -> Dict[str, List[float]]:
        # Forward: Palm center to MiddleMCP
        # Right: IndexMCP to PinkyMCP
        palm_center = self._calculate_palm_center(coords)
        forward = coords[9] - palm_center
        forward = forward / (np.linalg.norm(forward) + 1e-6)
        
        right = coords[17] - coords[5]
        right = right / (np.linalg.norm(right) + 1e-6)
        
        up = np.cross(forward, right)
        up = up / (np.linalg.norm(up) + 1e-6)
        
        # We explicitly preserve these as features so the model knows the absolute orientation
        return {
            "forward": forward.tolist(),
            "right": right.tolist(),
            "up": up.tolist()
        }

    def _normalize_hand(self, landmarks_list, label: str) -> Dict[str, Any]:
        coords = np.array([[lm.x, lm.y, lm.z] for lm in landmarks_list.landmark], dtype=np.float32)
        
        palm_center = self._calculate_palm_center(coords)
        scale = self._calculate_scale(coords)
        
        # 1. Translation Normalization (center at palm)
        # 2. Scale Normalization (divide by scale)
        # Depth is implicitly normalized since z is scaled by the same factor
        norm_coords = (coords - palm_center) / scale
        
        # Calculate derived geometric features
        # Finger lengths & states
        finger_states = {}
        tips = {"thumb": 4, "index": 8, "middle": 12, "ring": 16, "pinky": 20}
        bases = {"thumb": 1, "index": 5, "middle": 9, "ring": 13, "pinky": 17}
        
        for name, tip_idx in tips.items():
            base_idx = bases[name]
            dist = np.linalg.norm(norm_coords[tip_idx] - norm_coords[base_idx])
            # Simple geometric heuristic for extended/flexed
            state = "extended" if dist > 1.2 else ("flexed" if dist < 0.6 else "curved")
            finger_states[name] = {"state": state, "extension_ratio": round(float(dist), 2)}

        # Handedness mirroring fix
        # Note: Mediapipe identifies handedness on the mirrored image correctly if flipping is done properly.
        # But we pass the label explicitly.
        
        return {
            "handedness": label,
            "palm_center_image_space": palm_center.tolist(),
            "scale": float(scale),
            "orientation": self._calculate_orientation(coords),
            "finger_states": finger_states,
            "normalized_landmarks": norm_coords.tolist()
        }

    def process(self, multi_lms, multi_handedness) -> Dict[str, Any]:
        timestamp = time.perf_counter()
        
        frame_data = {
            "timestamp": timestamp,
            "hands": {}
        }
        
        if multi_lms and multi_handedness:
            for idx, hand_handedness in enumerate(multi_handedness):
                label = hand_handedness.classification[0].label.lower() # 'left' or 'right'
                lms = multi_lms[idx]
                frame_data["hands"][label] = self._normalize_hand(lms, label)

        # Relational Geometry
        if "left" in frame_data["hands"] and "right" in frame_data["hands"]:
            left_pc = np.array(frame_data["hands"]["left"]["palm_center_image_space"])
            right_pc = np.array(frame_data["hands"]["right"]["palm_center_image_space"])
            dist = np.linalg.norm(right_pc - left_pc)
            
            # Normalize by average scale
            avg_scale = (frame_data["hands"]["left"]["scale"] + frame_data["hands"]["right"]["scale"]) / 2.0
            frame_data["two_hand_relationship"] = {
                "distance_normalized": float(dist / max(avg_scale, 1e-6)),
                "delta_x": float((right_pc[0] - left_pc[0]) / avg_scale),
                "delta_y": float((right_pc[1] - left_pc[1]) / avg_scale)
            }
        
        self.history.append(frame_data)
        
        # Calculate motion
        motion = {}
        if len(self.history) >= 2:
            prev = self.history[-2]
            dt = max(1e-4, timestamp - prev["timestamp"])
            
            for side in ["left", "right"]:
                if side in frame_data["hands"] and side in prev["hands"]:
                    curr_pc = np.array(frame_data["hands"][side]["palm_center_image_space"])
                    prev_pc = np.array(prev["hands"][side]["palm_center_image_space"])
                    vel = (curr_pc - prev_pc) / dt
                    motion[side] = {
                        "velocity": vel.tolist(),
                        "speed": float(np.linalg.norm(vel))
                    }
        frame_data["motion"] = motion
        
        return {
            "current_frame": frame_data,
            "temporal_history_length": len(self.history)
        }
    
    def get_crop_box(self, multi_lms, img_w: int, img_h: int) -> Optional[tuple]:
        """Returns (x_min, y_min, x_max, y_max) with padding around all hands"""
        if not multi_lms:
            return None
            
        x_coords = []
        y_coords = []
        for lms in multi_lms:
            for lm in lms.landmark:
                x_coords.append(lm.x * img_w)
                y_coords.append(lm.y * img_h)
                
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)
        
        box_w = x_max - x_min
        box_h = y_max - y_min
        
        pad_x = box_w * 0.25
        pad_y = box_h * 0.25
        
        return (
            max(0, int(x_min - pad_x)),
            max(0, int(y_min - pad_y)),
            min(img_w, int(x_max + pad_x)),
            min(img_h, int(y_max + pad_y))
        )
