import numpy as np
from typing import List, Dict, Any, Optional
from collections import deque
import time

FEATURE_VECTOR_LENGTH = 180

class LandmarkFeatureExtractor:
    """
    Upgraded scale-invariant, position-invariant 3D landmark and temporal feature extractor.
    Extracts geometric hand poses, finger pinch/spread relationships, inter-hand metrics,
    and temporal velocity vectors for static and dynamic ASL/ISL gestures.
    """

    def __init__(self):
        self.feature_dim = FEATURE_VECTOR_LENGTH
        # Rolling history of wrist positions for velocity/motion calculation (stores (timestamp, left_wrist, right_wrist))
        self.history = deque(maxlen=6)

    def _get_finger_extensions(self, landmarks_np: np.ndarray, palm_scale: float) -> np.ndarray:
        """Calculates extension ratio of 5 fingers relative to wrist (scaled by palm size)."""
        extensions = np.zeros(5, dtype=np.float32)
        wrist = landmarks_np[0]

        # Finger tips: 4, 8, 12, 16, 20
        tip_indices = [4, 8, 12, 16, 20]
        for i, tip_idx in enumerate(tip_indices):
            dist = np.linalg.norm(landmarks_np[tip_idx] - wrist)
            extensions[i] = float(dist / (palm_scale + 1e-6))
        return extensions

    def _get_pinch_distances(self, landmarks_np: np.ndarray, palm_scale: float) -> np.ndarray:
        """Calculates normalized distances from thumb tip (4) to other finger tips (8, 12, 16, 20)."""
        pinches = np.zeros(4, dtype=np.float32)
        thumb_tip = landmarks_np[4]
        for i, tip_idx in enumerate([8, 12, 16, 20]):
            dist = np.linalg.norm(landmarks_np[tip_idx] - thumb_tip)
            pinches[i] = float(dist / (palm_scale + 1e-6))
        return pinches

    def _get_finger_spreads(self, landmarks_np: np.ndarray, palm_scale: float) -> np.ndarray:
        """Calculates distances between adjacent fingertips: (8-12), (12-16), (16-20), (8-20)."""
        spreads = np.zeros(4, dtype=np.float32)
        pairs = [(8, 12), (12, 16), (16, 20), (8, 20)]
        for i, (f1, f2) in enumerate(pairs):
            dist = np.linalg.norm(landmarks_np[f1] - landmarks_np[f2])
            spreads[i] = float(dist / (palm_scale + 1e-6))
        return spreads

    def _get_palm_normal(self, landmarks_np: np.ndarray) -> np.ndarray:
        """Computes 3D normal vector to the palm surface using wrist(0), index MCP(5), and pinky MCP(17)."""
        v1 = landmarks_np[5] - landmarks_np[0]
        v2 = landmarks_np[17] - landmarks_np[0]
        normal = np.cross(v1, v2)
        norm = np.linalg.norm(normal)
        if norm > 1e-6:
            return normal / norm
        return np.zeros(3, dtype=np.float32)

    def extract_features(self, multi_hand_landmarks, multi_handedness, timestamp: Optional[float] = None) -> np.ndarray:
        """
        Extracts deterministic 180-dimensional feature vector.
        Ensures exact identical structure between training and inference.
        """
        features = np.zeros(self.feature_dim, dtype=np.float32)
        if timestamp is None:
            timestamp = time.perf_counter()

        left_lms = None
        right_lms = None

        if multi_hand_landmarks and multi_handedness:
            for idx, hand_handedness in enumerate(multi_handedness):
                label = hand_handedness.classification[0].label  # 'Left' or 'Right'
                lms = multi_hand_landmarks[idx]
                coords = np.array([[lm.x, lm.y, lm.z] for lm in lms.landmark], dtype=np.float32)
                # Sanity check: replace NaNs/Infs
                coords = np.nan_to_num(coords, nan=0.0, posinf=0.0, neginf=0.0)

                if label == "Left":
                    left_lms = coords
                else:
                    right_lms = coords

        # Helper to extract single hand features (80 values)
        def extract_hand_slot(landmarks_np: Optional[np.ndarray], start_idx: int):
            if landmarks_np is None:
                return

            features[start_idx] = 1.0  # presence flag
            wrist = landmarks_np[0]
            palm_scale = float(np.linalg.norm(landmarks_np[9] - wrist))
            if palm_scale < 1e-4:
                palm_scale = 1.0

            # 63 normalized relative coords (1..63)
            norm_coords = (landmarks_np - wrist) / palm_scale
            features[start_idx + 1: start_idx + 64] = norm_coords.flatten()

            # 5 extension ratios (64..68)
            exts = self._get_finger_extensions(landmarks_np, palm_scale)
            features[start_idx + 64: start_idx + 69] = exts

            # 4 pinch distances (69..72)
            pinches = self._get_pinch_distances(landmarks_np, palm_scale)
            features[start_idx + 69: start_idx + 73] = pinches

            # 4 finger spreads (73..76)
            spreads = self._get_finger_spreads(landmarks_np, palm_scale)
            features[start_idx + 73: start_idx + 77] = spreads

            # 3 palm normal vector (77..79)
            normal = self._get_palm_normal(landmarks_np)
            features[start_idx + 77: start_idx + 80] = normal

        # Slot 1: Left Hand (indices 0 to 79)
        extract_hand_slot(left_lms, 0)

        # Slot 2: Right Hand (indices 80 to 159)
        extract_hand_slot(right_lms, 80)

        # Slot 3: Inter-Hand Relational Features (indices 160 to 169)
        if left_lms is not None and right_lms is not None:
            features[160] = 1.0  # both hands present flag
            wrist_diff = right_lms[0] - left_lms[0]
            features[161:164] = wrist_diff  # dx, dy, dz
            features[164] = float(np.linalg.norm(wrist_diff))  # wrist distance
            features[165] = float(np.linalg.norm(right_lms[8] - left_lms[8]))  # index tip distance
            features[166] = float(np.linalg.norm(right_lms[4] - left_lms[4]))  # thumb tip distance
            features[167] = abs(float(right_lms[0][1] - left_lms[0][1]))       # vertical elevation delta
            features[168] = float(right_lms[0][0] - left_lms[0][0])            # horizontal spread
            features[169] = float(np.dot(self._get_palm_normal(left_lms), self._get_palm_normal(right_lms)))  # normal alignment

        # Slot 4: Dynamic Temporal Motion Features (indices 170 to 179)
        # Update history
        left_wrist_pos = left_lms[0] if left_lms is not None else None
        right_wrist_pos = right_lms[0] if right_lms is not None else None
        self.history.append((timestamp, left_wrist_pos, right_wrist_pos))

        if len(self.history) >= 2:
            prev_t, prev_lw, prev_rw = self.history[0]
            dt = max(1e-4, timestamp - prev_t)

            if right_lms is not None and prev_rw is not None:
                vel_r = (right_lms[0] - prev_rw) / dt
                features[170:173] = np.clip(vel_r, -10.0, 10.0)
                features[173] = float(np.linalg.norm(features[170:173]))  # right hand speed

            if left_lms is not None and prev_lw is not None:
                vel_l = (left_lms[0] - prev_lw) / dt
                features[174:177] = np.clip(vel_l, -10.0, 10.0)
                features[177] = float(np.linalg.norm(features[174:177]))  # left hand speed

            # Combined velocity delta
            features[178] = features[173] - features[177]
            features[179] = max(features[173], features[177])  # dominant movement speed

        # Ensure final safety: clean any NaNs or Infs
        return np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)
