@echo off
echo 🌪️ Starting Wind Tunnel Data Explorer...

echo Checking if Python is installed...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    pause
    exit /b 1
)

echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo ⚠️  Make sure Ollama is running with Gemma3 model!
echo    Run these commands in another terminal:
echo    1. ollama serve
echo    2. ollama pull gemma3:1b
echo.

echo 🚀 Starting Flask app...
python flask_app.py

pause
