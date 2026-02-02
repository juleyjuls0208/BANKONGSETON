@echo off
echo ========================================
echo BANGKO NG SETON - Local Admin Dashboard
echo ========================================
echo.
echo This will start the FULL dashboard with Arduino support
echo on your local PC (http://localhost:5000)
echo.
echo Make sure:
echo  - Arduino is connected to USB
echo  - RFID reader is working
echo.
echo Press Ctrl+C to stop
echo.
pause

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

cd /d "%~dp0..\backend\dashboard"

echo.
echo Starting local dashboard with Arduino...
echo.

python admin_dashboard.py

pause
