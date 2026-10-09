import os
import sys
import time
import socket
import threading
import webbrowser
import multiprocessing
import traceback
from pathlib import Path

# Provide freeze_support for PyInstaller before importing other complex libraries
multiprocessing.freeze_support()

def setup_logging():
    app_data = Path(os.environ.get("APPDATA", str(Path.home())))
    log_dir = app_data / "SIGNBRIDGE" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "startup.log"
    return log_file

class LoggerTee:
    def __init__(self, filename, stream):
        self.stream = stream
        self.log_file = open(filename, 'a', encoding='utf-8')
    def write(self, message):
        self.stream.write(message)
        self.log_file.write(message)
        self.log_file.flush()
    def flush(self):
        self.stream.flush()
        self.log_file.flush()

def get_free_port(start_port=8000, max_port=8100):
    for port in range(start_port, max_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    raise RuntimeError("No free port available.")

def check_ollama(timeout=2.0):
    try:
        import httpx
        host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        res = httpx.get(f"{host}/api/tags", timeout=timeout)
        if res.status_code == 200:
            return True, "Running"
        return False, f"HTTP {res.status_code}"
    except ImportError:
        return False, "httpx not installed"
    except Exception as e:
        return False, "Not reachable"

def check_vision_model(timeout=2.0):
    try:
        import httpx
        host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        model_name = os.getenv("OLLAMA_VISION_MODEL", "qwen2.5vl:3b")
        res = httpx.get(f"{host}/api/tags", timeout=timeout)
        if res.status_code == 200:
            data = res.json()
            models = [m.get("name") for m in data.get("models", [])]
            if model_name in models or f"{model_name}:latest" in models:
                return True, "Available"
            return False, f"Missing '{model_name}'"
    except Exception:
        return False, "Ollama down"
    return False, "Unknown error"

def startup_monitor(port, host, server):
    url = f"http://{host}:{port}"
    print("[*] Application files: READY")
    print("[*] Python runtime: READY")
    print(f"[*] Backend: STARTING on {url}")
    
    ollama_ok, ollama_status = check_ollama()
    print(f"[*] Ollama server: {'READY' if ollama_ok else 'UNAVAILABLE'} ({ollama_status})")
    
    vision_ok, vision_status = check_vision_model()
    print(f"[*] Vision model: {'READY' if vision_ok else 'UNAVAILABLE'} ({vision_status})")
    
    if not ollama_ok:
        print("\n[!] Note: Ollama is not running. Core sign recognition (ASL/ISL) will still work!")
        print("          Start Ollama manually to enable full neural translation features.")
    elif not vision_ok:
        print("\n[!] Note: Vision model is not downloaded. Run 'ollama pull qwen2.5vl:3b' to enable vision-assist.")
        
    print("\n[*] Camera: Waiting for browser permission...")

    # Poll health endpoint
    health_url = f"{url}/api/health"
    start_time = time.time()
    backend_ready = False
    
    import httpx
    while time.time() - start_time < 30:
        try:
            res = httpx.get(health_url, timeout=1.0)
            if res.status_code == 200:
                backend_ready = True
                break
        except Exception:
            pass
        time.sleep(0.5)

    if backend_ready:
        print(f"\n[OK] Backend is ready! Opening browser at {url} ...")
        webbrowser.open(url)
    else:
        print("\n[ERROR] Backend failed to start within 30 seconds.")
        server.should_exit = True

def main():
    log_file = setup_logging()
    
    sys.stdout = LoggerTee(log_file, sys.stdout)
    sys.stderr = LoggerTee(log_file, sys.stderr)

    print("\n" + "="*50)
    print(f" SIGNBRIDGE STARTUP - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50 + "\n")

    try:
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys._MEIPASS)
        else:
            base_dir = Path(__file__).resolve().parent.parent
        
        os.environ["BASE_DIR"] = str(base_dir)

        # Find a free port safely
        port = get_free_port(start_port=8000)
        host = "127.0.0.1"
        
        os.environ["PORT"] = str(port)
        os.environ["HOST"] = host
        
        # Import uvicorn and our app late so freeze_support happens first
        import uvicorn
        from backend.main import app
        
        # We use log_level="warning" so the user doesn't get flooded with HTTP requests 
        # and instead sees our clean startup summary.
        config = uvicorn.Config(app=app, host=host, port=port, log_level="warning")
        server = uvicorn.Server(config)
        
        monitor_thread = threading.Thread(target=startup_monitor, args=(port, host, server), daemon=True)
        monitor_thread.start()
        
        server.run()
    except KeyboardInterrupt:
        print("\n[*] Shutting down SIGNBRIDGE...")
    except Exception as e:
        print(f"\n[ERROR] Server exited with error: {e}")
        traceback.print_exc()
        print(f"\nCheck logs at: {log_file}")
        
        # Keep window open if it failed
        print("\nPress Enter to exit...")
        sys.stdin.readline()

if __name__ == "__main__":
    main()
