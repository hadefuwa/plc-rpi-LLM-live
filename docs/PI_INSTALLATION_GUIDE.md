# Raspberry Pi Installation Guide
## PLC E-Stop AI Status Reporter

This guide will help you install your PLC monitoring application on a Raspberry Pi. The process is designed to be simple and beginner-friendly.

## What This App Does

Your app is a **PLC monitoring system** that:
- Connects to Siemens S7 PLCs over the network
- Shows real-time status of your industrial equipment
- Uses AI to analyze data and generate reports
- Runs completely offline (no internet required after setup)
- Starts automatically when the Pi boots up

## Prerequisites

- Raspberry Pi (any model with 2GB+ RAM recommended)
- MicroSD card with Raspberry Pi OS installed
- Network connection to your PLC
- Basic familiarity with terminal/command line

## Installation Steps

### Step 1: Prepare Your Raspberry Pi

1. **Boot up your Raspberry Pi** and log in
2. **Open a terminal** (click the terminal icon or press Ctrl+Alt+T)
3. **Update your system**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

### Step 2: Transfer Your App Files

You have two options to get your app files onto the Pi:

#### Option A: Using Git (Recommended)
```bash
# Clone your repository
git clone https://github.com/yourusername/plc-rpi-LLM-live.git
cd plc-rpi-LLM-live
```

#### Option B: Using USB/SD Card
1. Copy your entire project folder to a USB drive
2. Insert the USB drive into your Pi
3. Copy the files to your home directory:
   ```bash
   cp -r /media/pi/USB_DRIVE_NAME/plc-rpi-LLM-live ~/
   cd ~/plc-rpi-LLM-live
   ```

### Step 3: Run the Installation Script

The installation script will do everything automatically:

```bash
# Make the script executable
chmod +x install_on_pi.sh

# Run the installation
./install_on_pi.sh
```

**What the script does:**
- Installs Python and required packages
- Installs Ollama AI service
- Creates a virtual environment
- Installs Python dependencies
- Sets up auto-startup service
- Configures desktop autostart

### Step 4: Start the Application

After installation, start the service:

```bash
# Start the PLC monitoring service
sudo systemctl start plc-estop.service

# Check if it's running
sudo systemctl status plc-estop.service
```

### Step 5: Access Your App

1. **Open a web browser** on your Pi
2. **Go to**: `http://localhost:5001`
3. **You should see** your PLC monitoring dashboard

## Configuration

### PLC Settings

1. In the web interface, click **"PLC Configuration"**
2. **Enter your PLC details**:
   - IP Address: Your PLC's IP address (e.g., 192.168.1.100)
   - Rack Number: Usually 0
   - Slot Number: Usually 1
3. **Click "Test Connection"** to verify

### IO Mapping

Configure what signals to monitor:

1. **Add IO Points**:
   - Name: "E_Stop_Status"
   - Type: "bit"
   - Address: "DB1.DBX0.0"
   - Description: "Emergency stop button"

2. **Add more signals** as needed for your system

## Auto-Startup

Your app is configured to start automatically:

- **Service startup**: Starts when the Pi boots
- **Desktop startup**: Opens web browser automatically
- **AI service**: Ollama starts automatically

## Troubleshooting

### Check Service Status
```bash
# Check if the service is running
sudo systemctl status plc-estop.service

# View recent logs
sudo journalctl -u plc-estop.service -f
```

### Check Ollama AI Service
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama manually if needed
ollama serve
```

### Check Web Interface
```bash
# Test if the web server is responding
curl http://localhost:5001
```

### Common Issues

1. **"Connection failed" to PLC**:
   - Check PLC IP address
   - Verify network connectivity: `ping PLC_IP_ADDRESS`
   - Check firewall settings

2. **"AI not responding"**:
   - Start Ollama: `ollama serve`
   - Check model: `ollama list`

3. **"Service won't start"**:
   - Check logs: `sudo journalctl -u plc-estop.service`
   - Verify file permissions
   - Check Python dependencies

## Manual Commands

If you need to start/stop the app manually:

```bash
# Start the app manually
cd ~/plc-rpi-LLM-live
./start_plc_app.sh

# Stop the service
sudo systemctl stop plc-estop.service

# Restart the service
sudo systemctl restart plc-estop.service

# Disable auto-startup
sudo systemctl disable plc-estop.service

# Enable auto-startup
sudo systemctl enable plc-estop.service
```

## File Locations

- **App files**: `/home/pi/plc-rpi-LLM-live/`
- **Service file**: `/etc/systemd/system/plc-estop.service`
- **Autostart file**: `/home/pi/.config/autostart/autostart-plc-app.desktop`
- **Configuration**: `/home/pi/plc-rpi-LLM-live/data/plc_config.json`
- **Logs**: Use `sudo journalctl -u plc-estop.service`

## Next Steps

1. **Configure your PLC connection** in the web interface
2. **Set up your IO mapping** for the signals you want to monitor
3. **Test the connection** to make sure it can read from your PLC
4. **Customize the interface** for your specific needs

## Support

If you run into issues:
1. Check the troubleshooting section above
2. Look at the service logs: `sudo journalctl -u plc-estop.service -f`
3. Verify your PLC network settings
4. Make sure all dependencies are installed correctly

Your PLC monitoring system is now ready to use! 🚀
