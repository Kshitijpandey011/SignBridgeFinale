import os
import sys
import json
import time
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, f1_score
import joblib

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.config import ASL_MODEL_PATH, ISL_MODEL_PATH
from backend.recognition.sign_vocabulary import get_sign_list
from backend.recognition.feature_extractor import LandmarkFeatureExtractor, FEATURE_VECTOR_LENGTH

extractor = LandmarkFeatureExtractor()

def synthesize_hand_landmarks(
    wrist: Tuple[float, float, float] = (0.5, 0.7, 0.0),
    thumb: float = 0.0,
    index: float = 0.0,
    middle: float = 0.0,
    ring: float = 0.0,
    pinky: float = 0.0,
    palm_facing: str = "camera",  # "camera", "side", "inward", "down"
    spread: float = 1.0,
    scale: float = 0.12
) -> np.ndarray:
    """
    Synthesizes authentic 21-landmark MediaPipe 3D coordinates for a human hand.
    curl values: 0.0 = fully extended, 1.0 = fully curled into palm.
    """
    lms = np.zeros((21, 3), dtype=np.float32)
    w_vec = np.array(wrist, dtype=np.float32)
    lms[0] = w_vec  # Wrist

    # Base palm MCP offsets relative to wrist
    mcp_offsets = [
        (-0.32 * spread, 0.22, 0.04),  # Thumb CMC (1)
        (-0.22 * spread, 0.60, 0.0),   # Index MCP (5)
        (0.00, 0.65, 0.0),             # Middle MCP (9)
        (0.20 * spread, 0.60, 0.0),    # Ring MCP (13)
        (0.36 * spread, 0.52, 0.0)     # Pinky MCP (17)
    ]

    # Finger configurations: (MCP, PIP, DIP, TIP, curl, base_dir)
    finger_configs = [
        (1, 2, 3, 4, thumb, np.array([-0.20 * spread, 0.22, 0.08], dtype=np.float32)),
        (5, 6, 7, 8, index, np.array([-0.05 * spread, 0.24, -0.01], dtype=np.float32)),
        (9, 10, 11, 12, middle, np.array([0.00, 0.26, -0.01], dtype=np.float32)),
        (13, 14, 15, 16, ring, np.array([0.05 * spread, 0.24, -0.01], dtype=np.float32)),
        (17, 18, 19, 20, pinky, np.array([0.15 * spread, 0.20, -0.01], dtype=np.float32))
    ]

    for cmc, pip, dip, tip, curl, dir_vec in finger_configs:
        mcp_idx = cmc
        mcp_off = np.array(mcp_offsets[0 if mcp_idx == 1 else (mcp_idx - 1) // 4], dtype=np.float32)
        lms[mcp_idx] = w_vec + mcp_off * scale

        d = dir_vec.copy()
        if curl > 0.4:
            # Curl finger inward toward palm
            curl_factor = min(1.0, curl)
            d[1] = -abs(d[1]) * 0.35 * curl_factor
            d[2] = 0.18 * curl_factor

        lms[pip] = lms[mcp_idx] + d * scale * 0.85
        lms[dip] = lms[pip] + d * scale * 0.70
        lms[tip] = lms[dip] + d * scale * 0.60

    # Adjust for palm orientation
    if palm_facing == "down":
        lms[:, 1] = -lms[:, 1] + 2 * w_vec[1]
    elif palm_facing == "inward":
        lms[:, 2] = -lms[:, 2] + 2 * w_vec[2]
    elif palm_facing == "side":
        lms[:, 0] = (lms[:, 0] - w_vec[0]) * 0.3 + w_vec[0]

    return lms

def build_feature_vector(
    left_lms: Optional[np.ndarray],
    right_lms: Optional[np.ndarray],
    vel_r: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    vel_l: Tuple[float, float, float] = (0.0, 0.0, 0.0)
) -> np.ndarray:
    """
    Computes deterministic 180-dim feature vector mathematically identical to LandmarkFeatureExtractor.
    """
    features = np.zeros(FEATURE_VECTOR_LENGTH, dtype=np.float32)

    def fill_hand(lms_np: Optional[np.ndarray], start_idx: int):
        if lms_np is None:
            return
        features[start_idx] = 1.0
        wrist = lms_np[0]
        palm_scale = float(np.linalg.norm(lms_np[9] - wrist))
        if palm_scale < 1e-4:
            palm_scale = 1.0

        # Normalized coordinates (63)
        features[start_idx + 1: start_idx + 64] = ((lms_np - wrist) / palm_scale).flatten()

        # Extensions (5)
        for i, tip_idx in enumerate([4, 8, 12, 16, 20]):
            features[start_idx + 64 + i] = float(np.linalg.norm(lms_np[tip_idx] - wrist) / palm_scale)

        # Pinches (4)
        thumb_tip = lms_np[4]
        for i, tip_idx in enumerate([8, 12, 16, 20]):
            features[start_idx + 69 + i] = float(np.linalg.norm(lms_np[tip_idx] - thumb_tip) / palm_scale)

        # Spreads (4)
        for i, (f1, f2) in enumerate([(8, 12), (12, 16), (16, 20), (8, 20)]):
            features[start_idx + 73 + i] = float(np.linalg.norm(lms_np[f1] - lms_np[f2]) / palm_scale)

        # Normal (3)
        v1 = lms_np[5] - wrist
        v2 = lms_np[17] - wrist
        n = np.cross(v1, v2)
        norm = np.linalg.norm(n)
        if norm > 1e-6:
            features[start_idx + 77: start_idx + 80] = n / norm

    fill_hand(left_lms, 0)
    fill_hand(right_lms, 80)

    # Inter-hand
    if left_lms is not None and right_lms is not None:
        features[160] = 1.0
        wrist_diff = right_lms[0] - left_lms[0]
        features[161:164] = wrist_diff
        features[164] = float(np.linalg.norm(wrist_diff))
        features[165] = float(np.linalg.norm(right_lms[8] - left_lms[8]))
        features[166] = float(np.linalg.norm(right_lms[4] - left_lms[4]))
        features[167] = abs(float(right_lms[0][1] - left_lms[0][1]))
        features[168] = float(right_lms[0][0] - left_lms[0][0])
        n_l = features[77:80]
        n_r = features[157:160]
        features[169] = float(np.dot(n_l, n_r))

    # Dynamic features
    features[170:173] = vel_r
    features[173] = float(np.linalg.norm(vel_r))
    features[174:177] = vel_l
    features[177] = float(np.linalg.norm(vel_l))
    features[178] = features[173] - features[177]
    features[179] = max(features[173], features[177])

    return np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)

def synthesize_sign_pose(sign: str, mode: str) -> np.ndarray:
    """Creates authentic canonical landmark configurations for each sign."""
    s = sign.upper()

    if mode == "ASL":
        if s == "HELLO":
            # Right hand open, fingers extended together upright, palm facing camera
            r = synthesize_hand_landmarks((0.6, 0.45, 0.0), thumb=0.1, index=0.0, middle=0.0, ring=0.0, pinky=0.0, spread=0.6)
            return build_feature_vector(None, r, vel_r=(0.2, 0.0, 0.0))
        elif s == "THANK_YOU":
            # Right hand flat open moving from chin forward
            r = synthesize_hand_landmarks((0.55, 0.48, -0.05), thumb=0.1, index=0.0, middle=0.0, ring=0.0, pinky=0.0, spread=0.5)
            return build_feature_vector(None, r, vel_r=(0.0, -0.1, 0.3))
        elif s == "YES":
            # Right fist nodding
            r = synthesize_hand_landmarks((0.58, 0.60, 0.0), thumb=1.0, index=1.0, middle=1.0, ring=1.0, pinky=1.0)
            return build_feature_vector(None, r, vel_r=(0.0, 0.25, 0.0))
        elif s == "NO":
            # Index & middle snap shut with thumb; ring/pinky curled
            r = synthesize_hand_landmarks((0.58, 0.55, 0.0), thumb=0.6, index=0.6, middle=0.6, ring=1.0, pinky=1.0)
            return build_feature_vector(None, r, vel_r=(0.0, 0.1, 0.0))
        elif s == "PLEASE":
            # Flat open hand on chest
            r = synthesize_hand_landmarks((0.50, 0.58, 0.0), thumb=0.1, index=0.0, middle=0.0, ring=0.0, pinky=0.0, spread=0.7)
            return build_feature_vector(None, r, vel_r=(0.15, 0.15, 0.0))
        elif s == "SORRY":
            # Closed fist on chest
            r = synthesize_hand_landmarks((0.50, 0.58, 0.0), thumb=0.9, index=1.0, middle=1.0, ring=1.0, pinky=1.0)
            return build_feature_vector(None, r, vel_r=(0.15, 0.15, 0.0))
        elif s == "HELP":
            # Two hands: left flat base, right thumbs-up fist on left palm
            l = synthesize_hand_landmarks((0.44, 0.68, 0.0), thumb=0.0, index=0.0, middle=0.0, ring=0.0, pinky=0.0, palm_facing="down")
            r = synthesize_hand_landmarks((0.46, 0.60, 0.0), thumb=0.0, index=1.0, middle=1.0, ring=1.0, pinky=1.0)
            return build_feature_vector(l, r, vel_r=(0.0, -0.2, 0.0), vel_l=(0.0, -0.2, 0.0))
        elif s == "I_LOVE_YOU":
            # Thumb, index, pinky extended
            r = synthesize_hand_landmarks((0.58, 0.52, 0.0), thumb=0.0, index=0.0, middle=1.0, ring=1.0, pinky=0.0, spread=1.2)
            return build_feature_vector(None, r)
        elif s == "PEACE":
            # Index and middle in V-shape
            r = synthesize_hand_landmarks((0.58, 0.52, 0.0), thumb=1.0, index=0.0, middle=0.0, ring=1.0, pinky=1.0, spread=1.3)
            return build_feature_vector(None, r)
        elif s == "GOOD":
            # Thumbs-up
            r = synthesize_hand_landmarks((0.58, 0.58, 0.0), thumb=0.0, index=1.0, middle=1.0, ring=1.0, pinky=1.0)
            return build_feature_vector(None, r)
        elif s == "BAD":
            # Thumbs-down
            r = synthesize_hand_landmarks((0.58, 0.58, 0.0), thumb=0.0, index=1.0, middle=1.0, ring=1.0, pinky=1.0, palm_facing="down")
            return build_feature_vector(None, r)
        elif s == "WATER":
            # W-shape: index, middle, ring extended
            r = synthesize_hand_landmarks((0.55, 0.48, 0.0), thumb=1.0, index=0.0, middle=0.0, ring=0.0, pinky=1.0, spread=1.1)
            return build_feature_vector(None, r)
        elif s == "STOP":
            # Left flat, right vertical chopping onto it
            l = synthesize_hand_landmarks((0.44, 0.65, 0.0), thumb=0.0, index=0.0, middle=0.0, ring=0.0, pinky=0.0)
            r = synthesize_hand_landmarks((0.46, 0.60, 0.0), thumb=0.0, index=0.0, middle=0.0, ring=0.0, pinky=0.0, palm_facing="side")
            return build_feature_vector(l, r, vel_r=(0.0, 0.3, 0.0))
        elif s == "MORE":
            # Both hands flat-O shape fingertips touching
            l = synthesize_hand_landmarks((0.46, 0.62, 0.0), thumb=0.7, index=0.7, middle=0.7, ring=0.7, pinky=0.7)
            r = synthesize_hand_landmarks((0.54, 0.62, 0.0), thumb=0.7, index=0.7, middle=0.7, ring=0.7, pinky=0.7)
            return build_feature_vector(l, r)
        elif s == "EAT":
            # Flat-O tapping mouth
            r = synthesize_hand_landmarks((0.52, 0.46, 0.0), thumb=0.75, index=0.75, middle=0.75, ring=0.75, pinky=0.75)
            return build_feature_vector(None, r, vel_r=(0.0, 0.15, 0.0))

    elif mode == "ISL":
        if s == "NAMASTE":
            # Both palms joined together
            l = synthesize_hand_landmarks((0.46, 0.60, 0.0), thumb=0.0, index=0.0, middle=0.0, ring=0.0, pinky=0.0, spread=0.5)
            r = synthesize_hand_landmarks((0.54, 0.60, 0.0), thumb=0.0, index=0.0, middle=0.0, ring=0.0, pinky=0.0, spread=0.5)
            return build_feature_vector(l, r)
        elif s == "FOOD":
            r = synthesize_hand_landmarks((0.52, 0.46, 0.0), thumb=0.8, index=0.8, middle=0.8, ring=0.8, pinky=0.8)
            return build_feature_vector(None, r, vel_r=(0.0, 0.15, 0.0))
        elif s == "GOOD":
            r = synthesize_hand_landmarks((0.58, 0.58, 0.0), thumb=0.0, index=1.0, middle=1.0, ring=1.0, pinky=1.0)
            return build_feature_vector(None, r)
        elif s == "BAD":
            # Pinky gesture or thumbs-down
            r = synthesize_hand_landmarks((0.58, 0.58, 0.0), thumb=1.0, index=1.0, middle=1.0, ring=1.0, pinky=0.0)
            return build_feature_vector(None, r)
        elif s == "HELP":
            l = synthesize_hand_landmarks((0.44, 0.68, 0.0), thumb=0.0, index=0.0, middle=0.0, ring=0.0, pinky=0.0)
            r = synthesize_hand_landmarks((0.46, 0.60, 0.0), thumb=0.0, index=1.0, middle=1.0, ring=1.0, pinky=1.0)
            return build_feature_vector(l, r, vel_r=(0.0, -0.2, 0.0))
        elif s == "HOME":
            # Fingertips touching in roof peak
            l = synthesize_hand_landmarks((0.42, 0.54, 0.0), thumb=0.0, index=0.0, middle=0.0, ring=0.0, pinky=0.0, palm_facing="side")
            r = synthesize_hand_landmarks((0.58, 0.54, 0.0), thumb=0.0, index=0.0, middle=0.0, ring=0.0, pinky=0.0, palm_facing="side")
            return build_feature_vector(l, r)
        elif s == "SCHOOL":
            # Clapping hands
            l = synthesize_hand_landmarks((0.47, 0.64, 0.0), thumb=0.0, index=0.0, middle=0.0, ring=0.0, pinky=0.0)
            r = synthesize_hand_landmarks((0.53, 0.64, 0.0), thumb=0.0, index=0.0, middle=0.0, ring=0.0, pinky=0.0)
            return build_feature_vector(l, r, vel_r=(-0.2, 0.0, 0.0), vel_l=(0.2, 0.0, 0.0))
        elif s == "SORRY":
            r = synthesize_hand_landmarks((0.50, 0.58, 0.0), thumb=0.9, index=1.0, middle=1.0, ring=1.0, pinky=1.0)
            return build_feature_vector(None, r, vel_r=(0.15, 0.15, 0.0))
        elif s == "THANK_YOU":
            r = synthesize_hand_landmarks((0.55, 0.48, -0.05), thumb=0.1, index=0.0, middle=0.0, ring=0.0, pinky=0.0, spread=0.5)
            return build_feature_vector(None, r, vel_r=(0.0, -0.1, 0.3))
        elif s == "WATER":
            r = synthesize_hand_landmarks((0.54, 0.48, 0.0), thumb=0.4, index=0.4, middle=0.4, ring=0.4, pinky=0.4)
            return build_feature_vector(None, r)
        elif s == "YES":
            r = synthesize_hand_landmarks((0.58, 0.60, 0.0), thumb=1.0, index=1.0, middle=1.0, ring=1.0, pinky=1.0)
            return build_feature_vector(None, r, vel_r=(0.0, 0.25, 0.0))
        elif s == "NO":
            r = synthesize_hand_landmarks((0.58, 0.52, 0.0), thumb=1.0, index=0.0, middle=1.0, ring=1.0, pinky=1.0)
            return build_feature_vector(None, r, vel_r=(0.2, 0.0, 0.0))
        elif s == "PLEASE":
            r = synthesize_hand_landmarks((0.50, 0.58, 0.0), thumb=0.1, index=0.0, middle=0.0, ring=0.0, pinky=0.0, spread=0.6)
            return build_feature_vector(None, r)
        elif s == "HELLO":
            r = synthesize_hand_landmarks((0.60, 0.46, 0.0), thumb=0.1, index=0.0, middle=0.0, ring=0.0, pinky=0.0, spread=0.7)
            return build_feature_vector(None, r, vel_r=(0.25, 0.0, 0.0))

    # Fallback
    r = synthesize_hand_landmarks((0.55, 0.55, 0.0))
    return build_feature_vector(None, r)

def augment_features(base_vec: np.ndarray, num_variations: int = 180) -> np.ndarray:
    """Generates realistic variations: spatial jitter, scale shifts, curl noise."""
    samples = []
    for _ in range(num_variations):
        sample = base_vec.copy()
        # Coordinate noise
        if sample[0] > 0.5:
            sample[1:64] += np.random.normal(0, 0.035, 63)
            sample[64:69] = np.clip(sample[64:69] + np.random.normal(0, 0.04, 5), 0.0, 2.5)
            sample[69:73] = np.clip(sample[69:73] + np.random.normal(0, 0.04, 4), 0.0, 2.5)
        if sample[80] > 0.5:
            sample[81:144] += np.random.normal(0, 0.035, 63)
            sample[144:149] = np.clip(sample[144:149] + np.random.normal(0, 0.04, 5), 0.0, 2.5)
            sample[149:153] = np.clip(sample[149:153] + np.random.normal(0, 0.04, 4), 0.0, 2.5)
        # Dynamic velocity jitter
        sample[170:180] += np.random.normal(0, 0.05, 10)
        samples.append(sample)
    return np.array(samples, dtype=np.float32)

def train_mode_model(mode: str, output_path: Path):
    print(f"\n==========================================")
    print(f"Training {mode} Recognition Model (180-dim feature vector)...")
    print(f"==========================================")

    signs = get_sign_list(mode)
    print(f"Target Vocabulary ({len(signs)} signs): {', '.join(signs)}")

    X_list = []
    y_list = []

    # Check for recorded custom data in data/{mode}/
    data_dir = BASE_DIR / "data" / mode.lower()
    custom_samples_count = 0
    if data_dir.exists():
        for sign_folder in data_dir.iterdir():
            if sign_folder.is_dir() and sign_folder.name in signs:
                npy_files = list(sign_folder.glob("*.npy"))
                for npy_file in npy_files:
                    feat = np.load(npy_file)
                    if feat.shape == (FEATURE_VECTOR_LENGTH,):
                        X_list.append(feat)
                        y_list.append(sign_folder.name)
                        custom_samples_count += 1

    print(f"Loaded {custom_samples_count} custom recorded samples from {data_dir}.")

    # Generate synthetic augmented samples for full vocabulary coverage
    samples_per_sign = 220
    for sign in signs:
        base_feat = synthesize_sign_pose(sign, mode)
        augmented = augment_features(base_feat, num_variations=samples_per_sign)
        for s in augmented:
            X_list.append(s)
            y_list.append(sign)

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list)

    print(f"Total training dataset size: {X.shape[0]} samples across {len(signs)} classes.")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    print("Fitting Random Forest Classifier (n_estimators=100)...")
    clf = RandomForestClassifier(n_estimators=100, max_depth=18, random_state=42, n_jobs=-1)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro")
    print(f"\n{mode} Test Set Accuracy: {acc * 100:.2f}% | Macro F1: {macro_f1 * 100:.2f}%")

    # Export model bundle
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        "model": clf,
        "classes": list(clf.classes_),
        "metadata": {
            "mode": mode,
            "feature_dim": FEATURE_VECTOR_LENGTH,
            "accuracy": round(float(acc), 4),
            "macro_f1": round(float(macro_f1), 4),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "classes": list(clf.classes_),
            "samples_trained": int(X.shape[0])
        }
    }

    joblib.dump(bundle, output_path, compress=3)
    print(f"Successfully saved {mode} model to: {output_path}")

    # Write config.json
    config_path = output_path.parent / "config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(bundle["metadata"], f, indent=2)
    print(f"Saved model config to: {config_path}")

def main():
    train_mode_model("ASL", ASL_MODEL_PATH)
    train_mode_model("ISL", ISL_MODEL_PATH)
    print("\nAll models trained and exported successfully!")

if __name__ == "__main__":
    main()
