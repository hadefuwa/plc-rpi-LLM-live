#!/bin/bash

# PLC E-Stop AI Status Reporter - Simple Run Script

echo "🚀 Starting PLC E-Stop AI Status Reporter..."

# Change to the application directory (go up one level from scripts folder)
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
    
    # Check and install missing dependencies
    echo "📦 Checking Python dependencies..."
    if ! python -c "import schedule" 2>/dev/null; then
        echo "Installing missing schedule module..."
        pip install schedule
    fi
    if ! python -c "import flask" 2>/dev/null; then
        echo "Installing missing flask module..."
        pip install flask
    fi
    if ! python -c "import snap7" 2>/dev/null; then
        echo "Installing missing snap7 module..."
        pip install python-snap7
    fi
    echo "✅ Dependencies verified"
else
    echo "⚠️  Virtual environment not found. Installing system-wide..."
    pip3 install -r requirements.txt --break-system-packages
fi

# Check if Ollama is running
echo "🤖 Checking Ollama service..."
if ! curl -s http://localhost:11434 > /dev/null; then
    echo "⚠️  Ollama is not running. Starting Ollama..."
    ollama serve &
    sleep 5
    echo "✅ Ollama started"
else
    echo "✅ Ollama is already running"
fi

# Check if Gemma model is available
echo "📥 Checking for Gemma3 model..."
if ! ollama list | grep -q "gemma3:1b"; then
    echo "📥 Downloading Gemma3 1B model..."
    ollama pull gemma3:1b
    echo "✅ Model downloaded"
else
    echo "✅ Gemma3 1B model is available"
fi

# Start Flask app
echo "🌐 Starting Flask app..."
python3 flask_app.py
