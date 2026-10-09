import os
import sys
import time
import cv2
import numpy as np
import httpx
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.config import ASL_MODEL_PATH, ISL_MODEL_PATH, OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_VISION_MODEL
from backend.recognition.sign_classifier import SignClassifierManager
from backend.recognition.feature_extractor import LandmarkFeatureExtractor
from backend.avatar.animation_planner import AvatarAnimationPlanner
from backend.translation.translator import TranslationManager
from backend.ollama.ollama_client import OllamaService

def print_header(title):
    print(f"\n{'='*55}\n  {title}\n{'='*55}")

def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print_header("SIGNBRIDGE SYSTEM VERIFICATION & BENCHMARK")
    passed = 0
    total = 0

    # 1. Models Check
    total += 1
    print("[1/6] Checking ASL and ISL Models...")
    mgr = SignClassifierManager()
    status = mgr.get_status()
    asl_ok = status.get("ASL", {}).get("available", False)
    isl_ok = status.get("ISL", {}).get("available", False)
    if asl_ok and isl_ok:
        print(f"  [OK] ASL Model Ready: {len(status['ASL']['classes'])} signs ({', '.join(status['ASL']['classes'][:5])}...)")
        print(f"  [OK] ISL Model Ready: {len(status['ISL']['classes'])} signs ({', '.join(status['ISL']['classes'][:5])}...)")
        passed += 1
    else:
        print(f"  [X] Models missing. Run: python scripts/train_models.py")

    # 2. Benchmark Inference Latency
    total += 1
    print("\n[2/6] Benchmarking Feature Extraction & Classifier Latency...")
    extractor = LandmarkFeatureExtractor()
    dummy_feat = np.random.normal(0, 0.1, 150).astype(np.float32)
    dummy_feat[80] = 1.0  # hand present

    times = []
    for _ in range(100):
        t0 = time.perf_counter()
        mgr.predict(dummy_feat, "ASL")
        times.append(time.perf_counter() - t0)

    avg_ms = (sum(times) / len(times)) * 1000
    fps_est = 1000 / avg_ms if avg_ms > 0 else 999
    print(f"  [OK] Average Inference Latency: {avg_ms:.2f} ms per frame (~{fps_est:.0f} FPS potential)")
    if avg_ms < 10:
        passed += 1
    else:
        print("  ! Latency higher than expected.")

    # 3. Camera Check
    total += 1
    print("\n[3/6] Checking Webcam Index 0...")
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret:
                print(f"  [OK] Webcam connected and captured frame: {frame.shape[1]}x{frame.shape[0]}")
                passed += 1
            else:
                print("  ! Webcam opened but frame read failed.")
        else:
            print("  ! Webcam index 0 not available.")
    except Exception as e:
        print(f"  ! Webcam check error: {e}")

    # 4. Ollama Service Check
    total += 1
    print(f"\n[4/6] Checking Local Ollama AI at {OLLAMA_HOST}...")
    try:
        res = httpx.get(f"{OLLAMA_HOST}/api/tags", timeout=3.0)
        if res.status_code == 200:
            models = [m["name"] for m in res.json().get("models", [])]
            print(f"  [OK] Ollama server online. Detected models: {', '.join(models)}")
            passed += 1
        else:
            print(f"  ! Ollama responded with HTTP {res.status_code}")
    except Exception:
        print("  ! Ollama server offline. Local fast-dictionary fallback will be used.")

    # 5. Translation & Indian Languages Check
    total += 1
    print("\n[5/6] Checking Translation Module...")
    try:
        ollama_svc = OllamaService()
        translator = TranslationManager(ollama_svc)
        langs = translator.get_supported_languages()
        print(f"  [OK] Supported Indian Languages ({len(langs)}): {', '.join(langs.keys())}")
        passed += 1
    except Exception as e:
        print(f"  ! Translation check failed: {e}")

    # 6. 3D Avatar Sequence Planner Check
    total += 1
    print("\n[6/6] Checking 3D Avatar Keyframe Dictionaries & Planner...")
    try:
        planner = AvatarAnimationPlanner()
        asl_cnt = len(planner.asl_dict)
        isl_cnt = len(planner.isl_dict)
        spell_cnt = len(planner.fingerspelling_dict)
        print(f"  [OK] ASL Keyframe Signs: {asl_cnt}")
        print(f"  [OK] ISL Keyframe Signs: {isl_cnt}")
        print(f"  [OK] Fingerspelling Alphabet: {spell_cnt} letters")

        # Test missing sign fallback
        test_plan = planner.plan_sequence("HELLO UNKNOWNWORD", "ASL")
        assert "UNKNOWNWORD" in test_plan["unavailable_words"]
        assert test_plan["sequence"][1]["type"] == "fingerspelling"
        print("  [OK] Missing sign fallback (fingerspelling) verified.")
        passed += 1
    except Exception as e:
        print(f"  ! Avatar planner failed: {e}")

    # Summary
    print_header("VERIFICATION SUMMARY")
    print(f"Score: {passed}/{total} Subsystems Healthy")
    if passed >= 5:
        print(">>> SIGNBRIDGE is fully operational and ready for use! <<<\n")
    else:
        print(">>> Please address missing components before running. <<<\n")

if __name__ == "__main__":
    main()
