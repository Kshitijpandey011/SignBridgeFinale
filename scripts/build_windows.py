import os
import subprocess
import sys
from pathlib import Path
import shutil

BASE_DIR = Path(__file__).resolve().parent.parent

def main():
    print("==================================================")
    print("      SIGNBRIDGE WINDOWS BUILD SCRIPT             ")
    print("==================================================")
    
    # 1. Install dependencies including pytest
    print("[*] Ensuring PyInstaller and dependencies are installed...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "httpx", "uvicorn", "fastapi", "websockets", "opencv-python", "mediapipe", "scikit-learn", "joblib", "pyttsx3", "python-dotenv", "pydantic", "pytest"])
    
    # 2. Run tests
    print("\n[*] Running automated tests...")
    test_result = subprocess.call([sys.executable, "-m", "pytest", "tests/"])
    if test_result != 0:
        print("[!] Tests failed. Aborting build.")
        sys.exit(1)
        
    # 3. Build the application
    print("\n[*] Building executable with PyInstaller...")
    
    launcher_path = BASE_DIR / "launcher" / "main.py"
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "SIGNBRIDGE",
        "--onedir",
        "--clean",
        "--noconfirm",
        "--add-data", f"{BASE_DIR / 'frontend'};frontend",
        "--add-data", f"{BASE_DIR / 'avatar' / 'dictionary'};avatar/dictionary",
        "--add-data", f"{BASE_DIR / 'models'};models",
        "--hidden-import", "backend.main",
        "--hidden-import", "uvicorn",
        "--hidden-import", "httpx",
        "--hidden-import", "websockets",
        "--hidden-import", "pyttsx3",
        str(launcher_path)
    ]
    
    subprocess.check_call(cmd, cwd=str(BASE_DIR))
    
    print("\n==================================================")
    print("[OK] PyInstaller build successful!")
    print(f"Executable is located at: {BASE_DIR / 'dist' / 'SIGNBRIDGE' / 'SIGNBRIDGE.exe'}")
    print("==================================================")

    # 3. Create installer if Inno Setup is available
    iscc_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe"
    ]
    iscc_path = next((p for p in iscc_paths if os.path.exists(p)), None)
    
    if iscc_path:
        print("\n[*] Inno Setup found. Building installer...")
        iss_path = BASE_DIR / "packaging" / "installer.iss"
        if iss_path.exists():
            subprocess.check_call([iscc_path, str(iss_path)], cwd=str(BASE_DIR))
            print("[OK] Installer generated successfully in dist/!")
        else:
            print("[!] Installer script not found at packaging/installer.iss")
    else:
        print("\n[!] Inno Setup not found. Skipping installer generation.")
        print("    To create an installer, install Inno Setup 6 and run this script again.")

if __name__ == "__main__":
    main()
