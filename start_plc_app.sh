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
    sudo systemctl start ollama
    sleep 5
fi

# Check if Gemma3 1B model is available
if ! ollama list | grep -q "gemma3:1b"; then
    echo "Downloading Gemma3 1B model..."
    ollama pull gemma3:1b
fi

# Start the Flask application
echo "Starting Flask application..."
python3 flask_app.py 