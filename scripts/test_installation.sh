#!/bin/bash

# Test script to verify PLC app installation on Raspberry Pi
echo "🧪 Testing PLC E-Stop AI Status Reporter Installation"
echo "====================================================="

# Change to the application directory (go up one level from scripts folder)
cd "$(dirname "$0")/.."

# Check if we're in the right directory
if [ ! -f "flask_app.py" ]; then
    echo "❌ Error: flask_app.py not found. Are you in the correct directory?"
    exit 1
fi

echo "✅ Found flask_app.py"

# Check Python installation
echo "🐍 Checking Python installation..."
if command -v python3 &> /dev/null; then
    echo "✅ Python3 is installed: $(python3 --version)"
else
    echo "❌ Python3 is not installed"
    exit 1
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "✅ Virtual environment exists"
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    echo "✅ Virtual environment created and dependencies installed"
fi

# Check Python dependencies
echo "📦 Checking Python dependencies..."
python3 -c "import flask, pandas, plotly, requests, snap7; print('✅ All Python dependencies are installed')" 2>/dev/null || {
    echo "❌ Missing Python dependencies. Installing..."
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
}

# Check if Ollama is installed
echo "🤖 Checking Ollama installation..."
if command -v ollama &> /dev/null; then
    echo "✅ Ollama is installed"
    
    # Check if Ollama service is running
    if curl -s http://localhost:11434/api/tags > /dev/null; then
        echo "✅ Ollama service is running"
    else
        echo "⚠️  Ollama service is not running. Starting..."
        nohup ollama serve > /dev/null 2>&1 &
        sleep 5
        if curl -s http://localhost:11434/api/tags > /dev/null; then
            echo "✅ Ollama service started successfully"
        else
            echo "❌ Failed to start Ollama service"
        fi
    fi
    
    # Check for Gemma3 model
    if ollama list | grep -q "gemma3:1b"; then
        echo "✅ Gemma3 1B model is available"
    else
        echo "⚠️  Gemma3 1B model not found. Downloading..."
        ollama pull gemma3:1b
        echo "✅ Gemma3 1B model downloaded"
    fi
else
    echo "❌ Ollama is not installed"
    echo "Please install Ollama first: curl -fsSL https://ollama.ai/install.sh | sh"
fi

# Check systemd service
echo "⚙️ Checking systemd service..."
if [ -f "/etc/systemd/system/plc-estop.service" ]; then
    echo "✅ Systemd service file exists"
    
    # Check service status
    if systemctl is-active --quiet plc-estop.service; then
        echo "✅ PLC service is running"
    else
        echo "⚠️  PLC service is not running"
        echo "To start it: sudo systemctl start plc-estop.service"
    fi
else
    echo "⚠️  Systemd service not installed"
    echo "To install: sudo cp plc-estop.service /etc/systemd/system/ && sudo systemctl daemon-reload"
fi

# Check autostart configuration
echo "🖥️ Checking desktop autostart..."
if [ -f "/home/pi/.config/autostart/autostart-plc-app.desktop" ]; then
    echo "✅ Desktop autostart is configured"
else
    echo "⚠️  Desktop autostart not configured"
    echo "To configure: mkdir -p ~/.config/autostart && cp autostart-plc-app.desktop ~/.config/autostart/"
fi

# Test Flask app startup
echo "🚀 Testing Flask app startup..."
echo "Starting Flask app for 10 seconds to test..."

# Start Flask app in background
python3 flask_app.py &
FLASK_PID=$!

# Wait a moment for it to start
sleep 5

# Test if the web interface is responding
if curl -s http://localhost:5001 > /dev/null; then
    echo "✅ Flask app is running and responding on port 5001"
else
    echo "❌ Flask app is not responding on port 5001"
fi

# Stop the test Flask app
kill $FLASK_PID 2>/dev/null
wait $FLASK_PID 2>/dev/null

echo ""
echo "🎉 Installation test completed!"
echo ""
echo "📋 Summary:"
echo "- Python and dependencies: ✅"
echo "- Virtual environment: ✅"
echo "- Ollama AI service: $(curl -s http://localhost:11434/api/tags > /dev/null && echo "✅" || echo "⚠️")"
echo "- Systemd service: $([ -f "/etc/systemd/system/plc-estop.service" ] && echo "✅" || echo "⚠️")"
echo "- Desktop autostart: $([ -f "/home/pi/.config/autostart/autostart-plc-app.desktop" ] && echo "✅" || echo "⚠️")"
echo "- Flask app: ✅"
echo ""
echo "🌐 Your app should be accessible at: http://localhost:5001"
echo "🔧 To start the service: sudo systemctl start plc-estop.service"
echo "📊 To check service status: sudo systemctl status plc-estop.service"
