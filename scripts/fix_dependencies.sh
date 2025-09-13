#!/bin/bash

# Quick fix script to install missing Python dependencies
# Run this on your Raspberry Pi when you get import errors

echo "🔧 Fixing Python dependencies..."
echo "================================="

# Change to the application directory
cd "$(dirname "$0")/.."

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "✅ Virtual environment found. Activating..."
    source venv/bin/activate
    
    echo "📦 Installing/updating Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo "✅ Verifying critical packages..."
    python -c "import schedule; print('✅ schedule: OK')" || echo "❌ schedule: FAILED"
    python -c "import flask; print('✅ flask: OK')" || echo "❌ flask: FAILED"
    python -c "import snap7; print('✅ snap7: OK')" || echo "❌ snap7: FAILED"
    python -c "import pandas; print('✅ pandas: OK')" || echo "❌ pandas: FAILED"
    python -c "import plotly; print('✅ plotly: OK')" || echo "❌ plotly: FAILED"
    python -c "import requests; print('✅ requests: OK')" || echo "❌ requests: FAILED"
    
    echo ""
    echo "🎉 Dependencies fixed! You can now run:"
    echo "   ./scripts/start_plc_app.sh"
    
else
    echo "❌ Virtual environment not found!"
    echo "Please run the full installation:"
    echo "   ./scripts/install_on_pi.sh"
fi
