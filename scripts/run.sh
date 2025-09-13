#!/bin/bash

# Wind Tunnel Data Explorer Startup Script

echo "🌪️ Starting Wind Tunnel Data Explorer..."

# Check if Ollama is running
echo "Checking Ollama service..."
if ! curl -s http://localhost:11434 > /dev/null; then
    echo "⚠️  Ollama is not running. Starting Ollama..."
    ollama serve &
    sleep 5
    echo "✅ Ollama started"
else
    echo "✅ Ollama is already running"
fi

# Check if Gemma model is available
echo "Checking for Gemma3 model..."
if ! ollama list | grep -q "gemma3:1b"; then
    echo "📥 Downloading Gemma3 1B model..."
    ollama pull gemma3:1b
    echo "✅ Model downloaded"
else
    echo "✅ Gemma3 1B model is available"
fi

# Change to the application directory (go up one level from scripts folder)
cd "$(dirname "$0")/.."

# Install Python dependencies if needed
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Start Flask app
echo "🚀 Starting Flask app..."
python3 flask_app.py
