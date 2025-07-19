#!/bin/bash

# PLC E-Stop AI Status Reporter - Startup Script for Raspberry Pi
# This script starts the application with proper environment setup

echo "Starting PLC E-Stop AI Status Reporter..."

# Change to the application directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Warning: Virtual environment not found. Using system Python."
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Starting Ollama service..."
    # Try systemctl first, if that fails, start manually
    if ! sudo systemctl start ollama 2>/dev/null; then
        echo "Systemctl failed, starting Ollama manually..."
        nohup ollama serve > /dev/null 2>&1 &
        sleep 10
    else
        sleep 5
    fi
fi

# Remove old Phi-3 model if it exists (to save space)
if ollama list | grep -q "phi3:mini"; then
    echo "Removing old Phi-3 model to save space..."
    ollama rm phi3:mini
fi

# Check if Gemma3 1B model is available
echo "Checking for Gemma3 1B model..."
if ! ollama list | grep -q "gemma3:1b"; then
    echo "Gemma3 1B model not found. Downloading..."
    ollama pull gemma3:1b
else
    echo "Gemma3 1B model already available."
fi

# Start the Flask application
echo "Starting Flask application..."
python3 flask_app.py 