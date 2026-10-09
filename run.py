import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def check_ollama():
    try:
        import httpx
        res = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        if res.status_code == 200:
            print("[OK] Ollama server is running locally.")
            return True
    except Exception:
        pass
    print("[!] Notice: Ollama server is not detected on http://localhost:11434.")
    print("    Sign recognition, 3D Avatar, and offline vocabulary translation will work normally.")
    print("    To enable full Ollama neural translation, run 'ollama serve' in another terminal.\n")
    return False

def verify_models():
    asl_model = BASE_DIR / "models" / "asl" / "asl_classifier.joblib"
    isl_model = BASE_DIR / "models" / "isl" / "isl_classifier.joblib"

    if not asl_model.exists() or not isl_model.exists():
        print("[*] Training starter ASL & ISL models now...")
        subprocess.run([sys.executable, str(BASE_DIR / "scripts" / "train_models.py")], check=True)
    else:
        print("[OK] Pretrained ASL and ISL models are ready.")

def main():
    print("\n" + "="*60)
    print("           SIGNBRIDGE - STARTUP CONTROLLER            ")
    print("  Unified ASL + ISL Sign Recognition, Translation & Avatar ")
    print("="*60 + "\n")

    verify_models()
    check_ollama()

    port = 8000
    host = "127.0.0.1"
    url = f"http://{host}:{port}"

    print(f"[*] Starting SIGNBRIDGE server on {url} ...")

    # Automatically open browser after 2 seconds
    def open_browser():
        time.sleep(1.8)
        print(f"[*] Opening browser dashboard at {url} ...")
        webbrowser.open(url)

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    import uvicorn
    uvicorn.run("backend.main:app", host=host, port=port, reload=False, log_level="info")

if __name__ == "__main__":
    main()
