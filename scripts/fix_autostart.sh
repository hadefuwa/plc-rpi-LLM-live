#!/bin/bash

# Fix Auto-Startup Script for PLC E-Stop AI Status Reporter
# This script reinstalls the systemd service with correct paths

echo "🔧 Fixing Auto-Startup for PLC E-Stop AI Status Reporter"
echo "========================================================"

# Change to the application directory
cd "$(dirname "$0")/.."

echo "📋 Reinstalling systemd service with correct paths..."

# Stop the service if it's running
sudo systemctl stop plc-estop.service 2>/dev/null

# Reinstall the service file
sudo cp deploy/plc-estop.service /etc/systemd/system/

# Reload systemd and enable the service
sudo systemctl daemon-reload
sudo systemctl enable plc-estop.service

# Start the service
sudo systemctl start plc-estop.service

# Check if it's running
sleep 3
if systemctl is-active plc-estop.service >/dev/null 2>&1; then
    echo "✅ Service is now running!"
else
    echo "❌ Service failed to start. Checking logs..."
    sudo journalctl -u plc-estop.service --no-pager -n 10
fi

echo ""
echo "📊 Service Status:"
sudo systemctl status plc-estop.service --no-pager

echo ""
echo "🎯 Next steps:"
echo "1. Reboot your Pi: sudo reboot"
echo "2. After reboot, check: sudo systemctl status plc-estop.service"
echo "3. Your app will be at: http://localhost:5001"
