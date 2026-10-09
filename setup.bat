@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo        SIGNBRIDGE INSTALLATION & SETUP CONTROLLER
echo ========================================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in PATH! Please install Python 3.10+
    pause
    exit /b 1
)
echo [OK] Python is available.

:: 2. Install dependencies
echo.
echo [*] Checking and installing Python dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Some dependencies had warnings during install.
)

:: 3. Train starter models if missing
echo.
echo [*] Verifying ASL and ISL models...
if not exist "models\asl\asl_classifier.joblib" (
    echo [*] Training initial ASL & ISL models...
    python scripts\train_models.py
) else (
    echo [OK] Sign language models are already trained and ready.
)

:: 4. Verify system
echo.
echo [*] Running system verification check...
python scripts\verify_system.py

echo.
echo ========================================================
echo           SETUP COMPLETE! Run run.bat to start.
echo ========================================================
pause
