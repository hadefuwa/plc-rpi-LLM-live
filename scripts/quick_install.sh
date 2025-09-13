#!/bin/bash

# PLC E-Stop AI Status Reporter - Quick Installation Script
# This script only installs what's missing, making it much faster

echo "⚡ Quick Install - PLC E-Stop AI Status Reporter"
echo "================================================"

# Change to the application directory
cd "$(dirname "$0")/.."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "📦 Installing Python3..."
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv
else
    echo "✅ Python3 already installed"
fi

# Check if required system packages are installed
echo "📦 Checking system packages..."
MISSING_PACKAGES=""
for package in curl git chromium-browser; do
    if ! dpkg -l | grep -q "^ii.*$package "; then
        MISSING_PACKAGES="$MISSING_PACKAGES $package"
    fi
done

if [ ! -z "$MISSING_PACKAGES" ]; then
    echo "📦 Installing missing packages:$MISSING_PACKAGES"
    sudo apt install -y $MISSING_PACKAGES
else
    echo "✅ All system packages already installed"
fi

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "🤖 Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
else
    echo "✅ Ollama already installed"
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
    source venv/bin/activate
    
    # Check if requirements are installed
    echo "📦 Checking Python dependencies..."
    if pip check &> /dev/null; then
        echo "✅ All Python dependencies are installed"
    else
        echo "📦 Installing missing Python dependencies..."
        pip install -r requirements.txt
    fi
fi

# Check if systemd service is installed
if [ ! -f "/etc/systemd/system/plc-estop.service" ]; then
    echo "⚙️ Installing systemd service..."
    sudo cp deploy/plc-estop.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable plc-estop.service
    echo "✅ Systemd service installed"
else
    echo "✅ Systemd service already installed"
fi

# Check if desktop autostart is configured
AUTOSTART_DIR="/home/pi/.config/autostart"
if [ ! -f "$AUTOSTART_DIR/autostart-plc-app.desktop" ]; then
    echo "🖥️ Setting up desktop autostart..."
    mkdir -p "$AUTOSTART_DIR"
    cp deploy/autostart-plc-app.desktop "$AUTOSTART_DIR/"
    echo "✅ Desktop autostart configured"
else
    echo "✅ Desktop autostart already configured"
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x scripts/*.sh

echo ""
echo "⚡ Quick installation completed!"
echo ""
echo "🚀 To start your app:"
echo "   ./scripts/start_plc_app.sh"
echo ""
echo "🔧 To start as service:"
echo "   sudo systemctl start plc-estop.service"
echo ""
echo "🌐 Web interface: http://localhost:5001"
