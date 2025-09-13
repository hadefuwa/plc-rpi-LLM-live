#!/bin/bash

# PLC E-Stop AI Status Reporter - Raspberry Pi Installation Script
# This script installs everything needed to run the PLC app on a Raspberry Pi

echo "🚀 Installing PLC E-Stop AI Status Reporter on Raspberry Pi..."
echo "================================================================"

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system packages
echo "📦 Installing required system packages..."
sudo apt install -y python3 python3-pip python3-venv curl git chromium-browser

# Install Ollama
echo "🤖 Installing Ollama AI service..."
curl -fsSL https://ollama.ai/install.sh | sh

# Create application directory
echo "📁 Setting up application directory..."
APP_DIR="/home/pi/plc-rpi-LLM-live"
mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Copy application files (assuming they're already in the current directory)
echo "📋 Copying application files..."
# Note: You'll need to copy your files here manually or via git clone

# Change to the application directory (go up one level from scripts folder)
cd "$(dirname "$0")/.."

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x start_plc_app.sh
chmod +x run.sh

# Install systemd service
echo "⚙️ Installing systemd service..."
sudo cp plc-estop.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable plc-estop.service

# Set up desktop autostart
echo "🖥️ Setting up desktop autostart..."
AUTOSTART_DIR="/home/pi/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
cp autostart-plc-app.desktop "$AUTOSTART_DIR/"

# Set proper permissions
echo "🔐 Setting proper permissions..."
sudo chown -R pi:pi "$APP_DIR"
chmod +x "$APP_DIR"/*.sh

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Copy your application files to: $APP_DIR"
echo "2. Start the service: sudo systemctl start plc-estop.service"
echo "3. Check status: sudo systemctl status plc-estop.service"
echo "4. View logs: sudo journalctl -u plc-estop.service -f"
echo ""
echo "🌐 The web interface will be available at: http://localhost:5000"
echo "🖥️ Desktop autostart will open Chromium browser automatically"
echo ""
echo "🔧 To manually start the app: cd $APP_DIR && ./scripts/start_plc_app.sh"
