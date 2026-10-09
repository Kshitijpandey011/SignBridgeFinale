@echo off
setlocal

echo ========================================================
echo                 STARTING SIGNBRIDGE
echo  Unified ASL + ISL Sign Recognition, Translation ^& 3D
echo ========================================================
echo.

:: Launch system through run.py
python run.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application exited with an error code: %errorlevel%
    pause
)
