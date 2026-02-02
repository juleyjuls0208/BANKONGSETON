@echo off
echo ====================================
echo   Bangko ng Seton - API Server
echo ====================================
echo.

REM Go to project root
cd /d "%~dp0.."

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
cd backend\api
pip install -q -r requirements_api.txt

REM Start API server
echo.
echo Starting API server...
echo.
python api_server.py

pause
