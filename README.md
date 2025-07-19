# E-Stop AI Status Reporter

A Python application running on a Raspberry Pi that monitors Siemens S7 PLC systems and generates intelligent operator reports when emergency stops are triggered. Features real-time IO monitoring, local AI analysis, and web-based reporting powered by local Large Language Models.

## What This App Does

When an E-Stop is pressed on a Siemens S7 PLC, this application:

- **Monitors E-Stop State**: Continuously polls the PLC for emergency stop activation
- **Reads System IO**: Captures all critical input/output states when E-Stop is triggered
- **Generates AI Reports**: Uses local LLM to create human-readable operator reports
- **Web Display**: Shows reports on a simple web interface accessible from any device on the LAN

## Key Features

### PLC Integration
- **Siemens S7 Support**: Compatible with S7-1200, S7-1500, S7-300, and S7-400 series
- **Real-time Monitoring**: Continuous polling of digital and analog inputs/outputs
- **Configurable IO**: Define which signals to monitor and report on
- **Ethernet Communication**: Direct IP connection to PLC

### AI-Powered Reporting
- **Local LLM Processing**: Uses Ollama with lightweight models (Phi-3 Mini recommended)
- **Intelligent Analysis**: Converts raw IO states into actionable operator reports
- **Custom Prompts**: Template-based reporting with system-specific context
- **Privacy-First**: All processing happens locally, no data leaves your network

### Web Interface
- **Flask Web Server**: Lightweight, responsive web application
- **Real-time Updates**: View latest E-Stop reports and system status
- **Mobile-Friendly**: Accessible from phones, tablets, and computers
- **Event Logging**: Optional history of E-Stop events and AI reports

## System Overview

### Hardware Requirements
- **Raspberry Pi**: 4 or 5 recommended for LLM performance (8GB RAM preferred)
- **Siemens S7 PLC**: 1200/1500/300/400 series with Ethernet capability
- **Network**: Ethernet connection between Pi and PLC on same subnet

### Software Stack
- **Python 3.x**: Core application framework
- **python-snap7**: S7 PLC communication library
- **Flask**: Web interface and API
- **Ollama**: Local LLM hosting (Gemma3 1B for Pi compatibility)
- **Chromium**: Full-screen kiosk browser
- **Systemd**: Auto-startup service management

## Quick Start

### Local Development (Windows/Linux)

1. **Clone the repository**
```bash
git clone https://github.com/hadefuwa/plc-rpi-LLM.git
cd plc-rpi-LLM
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Install and configure Ollama**
```bash
# Download and install Ollama from https://ollama.ai
ollama pull gemma3:1b
ollama serve
```

4. **Run the application**
```bash
python flask_app.py
```

5. **Access the web interface**
Open your browser and navigate to `http://localhost:5000`

### Raspberry Pi Deployment

1. **Prepare your Raspberry Pi**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh
```

2. **Clone and setup the project**
```bash
git clone https://github.com/hadefuwa/plc-rpi-LLM.git
cd plc-rpi-LLM

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

3. **Configure PLC connection**
```bash
# Edit config.py with your PLC IP address
nano config.py
```

4. **Setup Ollama and model**
```bash
# Start Ollama service
sudo systemctl enable ollama
sudo systemctl start ollama

# Pull the lightweight model
ollama pull gemma3:1b
```

5. **Setup Auto-Startup (Recommended)**
```bash
# Copy the service file to systemd
sudo cp plc-estop.service /etc/systemd/system/

# Reload systemd and enable the service
sudo systemctl daemon-reload
sudo systemctl enable plc-estop

# Start the service
sudo systemctl start plc-estop

# Check status
sudo systemctl status plc-estop
```

**Service Management Commands:**
```bash
# Start the service
sudo systemctl start plc-estop

# Stop the service
sudo systemctl stop plc-estop

# Restart the service
sudo systemctl restart plc-estop

# Check service status
sudo systemctl status plc-estop

# View service logs
sudo journalctl -u plc-estop -f

# Disable auto-startup
sudo systemctl disable plc-estop
```

## Auto-Start Chromium Browser (Kiosk Mode)

To automatically open the web interface in a browser when the Pi boots:

**1. Install Chromium (if not already installed):**
```bash
sudo apt update
sudo apt install chromium-browser -y
```

**2. Setup autostart directory:**
```bash
mkdir -p ~/.config/autostart
```

**3. Copy the autostart file:**
```bash
cp autostart-plc-app.desktop ~/.config/autostart/
```

**4. Make it executable:**
```bash
chmod +x ~/.config/autostart/autostart-plc-app.desktop
```

**5. Test the autostart (optional):**
```bash
# Test if the desktop file works
gtk-launch autostart-plc-app
```

**6. Reboot to test:**
```bash
sudo reboot
```

**Autostart Features:**
- **Full Screen**: Opens in maximized window
- **App Mode**: Runs as a standalone app (no browser UI)
- **Auto-Refresh**: Will reload if the page becomes unavailable
- **Kiosk Ready**: Perfect for wall-mounted displays

**To Disable Browser Autostart:**
```bash
rm ~/.config/autostart/autostart-plc-app.desktop
```

6. **Access the web interface**
Open your browser and navigate to `http://YOUR_PI_IP:5000`

## Easy Startup Scripts

### Windows
```bash
# Double-click or run:
run.bat
```

### Linux/Raspberry Pi
```bash
# Make executable and run:
chmod +x run.sh
./run.sh
```

## Configuration

### PLC Setup
1. **Enable Put/Get**: In TIA Portal > Device > Properties > Protection & Security
2. **Network Configuration**: Ensure Pi and PLC are on same subnet
3. **IP Address**: Configure static IP for reliable communication

### IO Configuration
Define which inputs/outputs to monitor in the application:

```python
# Example IO configuration
MONITORED_IO = {
    'inputs': {
        'emergency_stop': 'I0.0',
        'tank_level_low': 'I0.1', 
        'pump_running': 'I0.2',
        'valve_open': 'I0.3'
    },
    'outputs': {
        'motor_control': 'Q0.0',
        'alarm_relay': 'Q0.1',
        'valve_control': 'Q0.2'
    }
}
```

### AI Prompt Template
Customize the AI prompt for your specific system:

```python
PROMPT_TEMPLATE = """
The emergency stop has been pressed. Current system status:
{io_summary}

Please write a short operator report (2-3 sentences) summarizing:
1. Current system status
2. Immediate safety concerns
3. Recommended next actions
"""
```

## Functional Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   PLC       │    │   Python    │    │   Ollama    │    │   Web       │
│   E-Stop    │───▶│   Monitor   │───▶│   LLM       │───▶│   Display   │
│   Triggered │    │   & Read IO │    │   Analysis  │    │   Report    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### Step-by-Step Process
1. **E-Stop Detection**: Application continuously polls E-Stop input (e.g., I0.0)
2. **IO Reading**: On trigger, reads all configured digital/analog IO states
3. **Data Formatting**: Converts raw IO data into structured summary
4. **AI Analysis**: Sends formatted data to local LLM with prompt template
5. **Report Generation**: LLM generates human-readable operator report
6. **Web Display**: Shows report on Flask web interface

## Example AI Report

**Input Data:**
```
E-Stop: PRESSED
Pump Running: OFF
Tank Low Level: ON
Valve Open: OFF
Motor Control: OFF
Alarm Relay: ON
```

**AI Generated Report:**
```
EMERGENCY STOP ACTIVATED - System Status Report

The emergency stop has been triggered, immediately shutting down all motor operations. 
The pump is currently stopped and the tank level is critically low. 
The alarm relay is active, indicating system shutdown. 

IMMEDIATE ACTIONS REQUIRED:
1. Verify all personnel are safe and clear of equipment
2. Investigate cause of emergency stop activation
3. Check tank levels and refill if necessary
4. Reset E-Stop only after safety inspection is complete
```

## Deployment Notes

### Raspberry Pi Setup
- **Memory**: 8GB RAM recommended for LLM performance
- **Storage**: 32GB+ SD card for logs and application
- **Cooling**: Ensure adequate ventilation for sustained operation
- **Network**: Static IP configuration for reliable PLC communication

### PLC Configuration
- **Put/Get Access**: Must be enabled in TIA Portal
- **Network Security**: Configure appropriate firewall rules
- **IO Mapping**: Ensure monitored signals are properly configured
- **Backup**: Keep PLC program backups before testing

### Performance Considerations
- **LLM Response Time**: 5-15 seconds typical for lightweight models
- **Memory Usage**: ~2GB for LLM + 500MB for application
- **Network Latency**: Keep Pi and PLC on same subnet for low latency
- **Logging**: Monitor disk space for event logs

## Troubleshooting

### Common Issues

**PLC Connection Failed?**
- Verify IP address and network connectivity
- Check Put/Get is enabled in TIA Portal
- Ensure Pi and PLC are on same subnet
- Test with ping: `ping 192.168.1.100`

**AI Not Responding?**
- Verify Ollama is running: `ollama ps`
- Check model is installed: `ollama list`
- Test LLM connection: Visit `/test_ai` endpoint
- Monitor system resources: `htop`

**Web Interface Not Loading?**
- Check Flask is running: `python flask_app.py`
- Verify port 5000 is available
- Check firewall settings
- Access via: `http://[PI_IP]:5000`

**Slow Performance?**
- Close unnecessary applications
- Consider lighter LLM model (Phi-3 Mini)
- Monitor memory usage: `free -h`
- Ensure adequate cooling

## Future Enhancements

### Planned Features
- **Email Alerts**: Automatic report distribution via email
- **Historical Logging**: Database storage of all E-Stop events
- **Custom Scenarios**: Different AI prompts based on IO combinations
- **Mobile App**: Native mobile interface for operators
- **Integration**: Connect with SCADA or MES systems

### Advanced Features
- **Predictive Analysis**: AI prediction of potential issues
- **Multi-PLC Support**: Monitor multiple PLCs simultaneously
- **Custom Models**: Train specialized models for specific industries
- **Cloud Integration**: Optional cloud backup and analytics

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Commit changes: `git commit -m "Add feature"`
5. Push to branch: `git push origin feature-name`
6. Submit pull request

## License

MIT License - feel free to use for educational and commercial purposes.

## Acknowledgments

- **python-snap7**: For Siemens S7 PLC communication
- **Ollama Team**: For local AI model deployment
- **Flask Team**: For lightweight web framework
- **Microsoft**: For Phi-3 Mini language model

## Complete Industrial Kiosk Setup

This project creates a fully automated PLC monitoring kiosk perfect for industrial environments.

### What You Get After Setup

**🏭 Complete Industrial Solution:**
- **PLC Monitoring**: Real-time Siemens S7 PLC data monitoring
- **AI Analysis**: Local Gemma3 1B AI for intelligent reporting  
- **Web Dashboard**: Full-screen monitoring interface
- **Auto-Startup**: Starts automatically on every boot
- **Kiosk Mode**: Full-screen display ready for wall mounting
- **Network Access**: Accessible from any device on the network

**🎯 Perfect For:**
- Industrial control rooms
- Manufacturing floors
- Remote monitoring stations
- Wall-mounted displays
- Operator workstations

### Complete Setup Commands

**One-Command Setup (Copy & Paste):**
```bash
# Update and install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv chromium-browser -y

# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Clone and setup project
git clone https://github.com/hadefuwa/plc-rpi-LLM.git
cd plc-rpi-LLM
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup Ollama
sudo systemctl enable ollama
sudo systemctl start ollama
ollama pull gemma3:1b

# Setup auto-startup service
sudo cp plc-estop.service /etc/systemd/system/
chmod +x start_plc_app.sh
sudo systemctl daemon-reload
sudo systemctl enable plc-estop
sudo systemctl start plc-estop

# Setup Chromium kiosk mode
mkdir -p ~/.config/autostart
cp autostart-plc-app.desktop ~/.config/autostart/
chmod +x ~/.config/autostart/autostart-plc-app.desktop

# Reboot to test everything
sudo reboot
```

### Troubleshooting Guide

**Service Issues:**
```bash
# Check service status
sudo systemctl status plc-estop

# View service logs
sudo journalctl -u plc-estop -n 50

# If service fails to start, check logs
sudo journalctl -u plc-estop -f

# If port 5000 is in use, kill existing processes
sudo netstat -tlnp | grep :5000
sudo kill [PID_NUMBER]

# If Ollama isn't running
ollama serve &

# Test the startup script manually
./start_plc_app.sh
```

**Permission Issues:**
```bash
# Make startup script executable
chmod +x start_plc_app.sh

# Fix service permissions
sudo systemctl daemon-reload
sudo systemctl restart plc-estop
```

**Browser Issues:**
```bash
# Test if Chromium can access the app
curl http://localhost:5000

# Check if autostart file is executable
chmod +x ~/.config/autostart/autostart-plc-app.desktop
```

---

**Built for industrial safety and operational efficiency**

*Transform your PLC emergency stops into intelligent, actionable insights*
