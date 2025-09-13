#!/bin/bash

# PLC E-Stop AI Status Reporter - Quick Start Script
# This script just starts the app without any installation

echo "🚀 Starting PLC E-Stop AI Status Reporter..."
echo "============================================="

# Change to the application directory
cd "$(dirname "$0")/.."

# Activate virtual environment
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️  Virtual environment not found. Using system Python."
fi

# Check if Ollama is running
echo "🤖 Checking Ollama..."
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Starting Ollama..."
    nohup ollama serve > /dev/null 2>&1 &
    sleep 5
    echo "✅ Ollama started"
else
    echo "✅ Ollama already running"
fi

# Check if Gemma3 model is available
if ! ollama list | grep -q "gemma3:1b"; then
    echo "📥 Downloading Gemma3 1B model..."
    ollama pull gemma3:1b
else
    echo "✅ Gemma3 1B model available"
fi

# Start Flask app
echo "🌐 Starting Flask app..."
echo "Web interface will be available at: http://localhost:5001"
python3 flask_app.py
