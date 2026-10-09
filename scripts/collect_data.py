import os
import sys
import time
from pathlib import Path
import cv2
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.recognition.landmark_detector import LandmarkDetector
from backend.recognition.feature_extractor import LandmarkFeatureExtractor
from backend.recognition.sign_vocabulary import get_sign_list

def collect_sign_samples(mode: str = "ASL", target_sign: str = "HELLO", num_samples: int = 50):
    mode_upper = mode.upper()
    valid_signs = get_sign_list(mode_upper)
    if target_sign not in valid_signs:
        print(f"Error: '{target_sign}' is not in the {mode_upper} vocabulary!")
        print(f"Available signs: {', '.join(valid_signs)}")
        return

    save_dir = BASE_DIR / "data" / mode_upper.lower() / target_sign
    save_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n=======================================================")
    print(f"Collecting {num_samples} samples for: {mode_upper} -> {target_sign}")
    print(f"Saving to: {save_dir}")
    print("Press SPACEBAR to start recording, 'q' to quit.")
    print("=======================================================\n")

    detector = LandmarkDetector()
    extractor = LandmarkFeatureExtractor()
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam index 0!")
        return

    recording = False
    samples_saved = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        lms, handedness, annotated = detector.process_frame(frame, draw_overlay=True)
        features = extractor.extract_features(lms, handedness)

        # Status text
        status_color = (0, 255, 0) if recording else (0, 200, 255)
        status_text = f"RECORDING ({samples_saved}/{num_samples})" if recording else "IDLE - Press SPACE to record"

        cv2.putText(annotated, f"Sign: {target_sign} [{mode_upper}]", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        cv2.putText(annotated, status_text, (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

        if recording and (features[0] > 0.5 or features[80] > 0.5):
            filename = save_dir / f"sample_{int(time.time()*1000)}_{samples_saved}.npy"
            np.save(filename, features)
            samples_saved += 1
            time.sleep(0.08)  # ~12 FPS recording rate

            if samples_saved >= num_samples:
                print(f"\n[DONE] Successfully saved {num_samples} samples for {target_sign}!")
                break

        cv2.imshow(f"SIGNBRIDGE Data Collector - {mode_upper}", annotated)
        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):
            recording = not recording
            print("Recording started..." if recording else "Paused.")
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    detector.close()

if __name__ == "__main__":
    mode_arg = sys.argv[1] if len(sys.argv) > 1 else "ASL"
    sign_arg = sys.argv[2] if len(sys.argv) > 2 else "HELLO"
    samples_arg = int(sys.argv[3]) if len(sys.argv) > 3 else 50
    collect_sign_samples(mode_arg, sign_arg, samples_arg)
