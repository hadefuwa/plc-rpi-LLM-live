# E-Stop AI Status Reporter

A comprehensive industrial automation monitoring and reporting system for Siemens S7-1200 PLC test rigs. This Flask-based web application combines real-time PLC monitoring with AI-powered analysis to provide intelligent operational insights and safety monitoring.

## 🎯 Core Purpose

Monitors a PLC-controlled test machine with safety systems (emergency stops, pumps, valves, motors) and uses AI to automatically analyze and report on system activity, focusing on safety status, operational changes, and system health.

## ✨ Key Features

### 🔧 **PLC Integration**
- **Real-time Monitoring**: Connects to Siemens S7-1200 PLC via Ethernet
- **Comprehensive I/O Support**: Digital I/O (buttons, switches, LEDs, relays) and analog inputs (flow rate, pressure, temperature)
- **Emergency Stop Tracking**: Critical priority alerts with automatic detection
- **Data Types**: Supports Bit, Byte, Word, DWord, and Real (32-bit IEEE float) values

### 🤖 **AI-Powered Analysis**
- **Automated Reports**: Every 15 minutes using Ollama with Gemma3 1B model
- **Configurable Intelligence**: Customizable system prompts and reporting intervals
- **Operational Insights**: Analyzes recent events, safety status, and system trends
- **Local Processing**: On-premises AI for industrial privacy and security

### 📊 **Web Dashboard**
- **Live Monitoring**: Real-time system status with color-coded indicators
- **Responsive Design**: Dark/light theme support with sticky navigation
- **Multi-page Interface**: Dashboard, PLC Config, System Status, Event Logs, Reports, AI Config
- **Connection Status**: Live PLC connection monitoring with visual indicators

### 📝 **Advanced Reporting System**
- **AI Reports**: Automated analysis showing operational patterns and recommendations
- **Data Reports**: Raw I/O snapshots in JSON format for technical analysis  
- **Event Logs**: Detailed change tracking with timestamps and priority levels
- **Report Archive**: Historical data with daily rotation and searchable logs

### ⚙️ **Configuration Management**
- **Web-based Setup**: PLC connection settings (IP, rack, slot) through browser
- **Dynamic I/O Mapping**: Custom descriptions and data type configuration
- **AI Configuration**: Report intervals, system prompts, and analysis parameters
- **I/O Grouping**: Organized monitoring with custom groups and categorization

## 🏗️ Technical Architecture

- **Backend**: Python Flask with multi-threading for real-time polling
- **PLC Communication**: Custom communicator using industrial S7 protocol
- **Data Storage**: JSON-based configuration with daily rotation event logging
- **AI Integration**: Local Ollama server for private, on-premises analysis
- **Frontend**: Responsive web interface with live updates and theme support
- **Deployment**: Raspberry Pi compatible with systemd service integration

## 🎯 Use Cases

- **Safety Monitoring**: Track emergency stop activations and system health compliance
- **Operational Analysis**: Understand test rig usage patterns and performance metrics
- **Maintenance Planning**: AI identifies potential issues and provides actionable recommendations
- **Industrial Compliance**: Automated logging for safety requirements and audit trails
- **Cost-Effective Monitoring**: Raspberry Pi deployment for budget-conscious industrial monitoring

## Quick Start

### Prerequisites

1. **Python 3.7 or higher** installed on your system
2. **Ollama** installed and running locally (for AI features)
3. **Network access** to your Siemens S7 PLC

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Ollama (for AI features)

If you want to use the AI analysis features, start Ollama with the Gemma3 1B model:

```bash
# Install Ollama (if not already installed)
# Visit: https://ollama.ai/download

# Pull the Gemma3 1B model
ollama pull gemma3:1b

# Start Ollama server
ollama serve
```

### 3. Start the Application

```bash
python flask_app.py
```

### 4. Access the Web Interface

Open your browser and go to: `http://localhost:5001`

## How to Use the Application

### Main Dashboard
- **System Overview**: View real-time system status and metrics
- **IO Status**: Monitor all configured PLC inputs and outputs
- **Event Log**: View recent system events and E-Stop activations
- **AI Analysis**: Ask questions about your system data
- **Connection Monitoring**: Live PLC connection status with visual indicators

### AI Reports System
- **Automated Generation**: AI reports generated every 15 minutes (configurable)
- **Full Content Display**: Latest 3 reports shown with complete analysis content
- **Manual Generation**: Generate reports on-demand via web interface
- **Report Archive**: Historical reports organized by date with searchable content
- **Intelligent Analysis**: Focuses on safety status, operational changes, system health, trend analysis, and maintenance recommendations

### AI Configuration
- **Custom Intervals**: Configure report generation frequency (minutes)
- **System Prompts**: Customize AI analysis focus and reporting style  
- **Event Analysis Limits**: Control how many recent events to analyze
- **Startup Delays**: Configure initialization timing for system stability

### PLC Configuration
1. Click **"PLC Configuration"** in the navigation menu
2. **Set PLC Connection**:
   - Enter your PLC's IP address
   - Set rack number (usually 0)
   - Set slot number (usually 1)
3. **Configure IO Mapping**:
   - Add your PLC addresses for each signal
   - Choose data type (Bit, Byte, Word, DWord)
   - Add descriptions for each signal
4. **Test Connection**: Use the "Test Connection" button to verify communication

### Supported PLC Address Formats

- **Bit (DBX)**: `DB1.DBX0.0` - Single bit reading
- **Byte (DBB)**: `DB1.DBB0` - 8-bit reading  
- **Word (DBW)**: `DB1.DBW0` - 16-bit reading
- **DWord (DBD)**: `DB1.DBD0` - 32-bit reading
 - **Real (DBD)**: `DB1.DBD30` - 32-bit IEEE float (uses the same DBD storage)

### Example IO Configuration

```json
{
  "E_Stop_Status": {
    "type": "bit",
    "address": "DB1.DBX0.0",
    "description": "Emergency stop activation"
  },
  "Pump_Running": {
    "type": "bit", 
    "address": "DB1.DBX0.1",
    "description": "Pump operational status"
  },
  "Flow_Rate": {
    "type": "word",
    "address": "DB1.DBW2",
    "description": "System flow rate in L/min"
  }
}
```

## File Structure

```
plc-rpi-LLM-live/
├── app/
│   ├── flask_app.py          # Main Flask application
│   ├── nav_template.py       # Shared navigation templates/styles
│   └── static/
│       └── favicon.ico       # App icon
├── core/
│   ├── config.py             # Configuration management
│   ├── plc_communicator.py   # PLC communication class
│   └── event_logger.py       # Event logging system
├── data/
│   ├── plc_config.json       # PLC configuration file (auto-generated)
│   └── io_events.json        # Event log storage
├── scripts/
│   ├── run.sh                # Linux/RPi startup script
│   ├── run.bat               # Windows startup script
│   └── start_plc_app.sh      # RPi service startup
├── deploy/
│   ├── plc-estop.service     # systemd service file
│   └── autostart-plc-app.desktop # desktop autostart file
├── CHANGELOG.md              # Project changelog
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Configuration

### PLC Settings

The system uses a JSON configuration file (`plc_config.json`) that is automatically created with default settings:

- **IP Address**: Set your PLC's IP address
- **Rack Number**: Usually 0 for most S7 PLCs
- **Slot Number**: Usually 1 for most S7 PLCs

### IO Mapping

Configure your PLC IO points through the web interface:

1. **IO Name**: Descriptive name for the signal
2. **Data Type**: Bit, Byte, Word, or DWord
3. **PLC Address**: Full address (e.g., `DB1.DBX0.0`)
4. **Description**: Human-readable description

## Troubleshooting

### PLC Connection Issues

1. **Check Network**: Ensure your device can ping the PLC IP
2. **Verify Settings**: Check rack/slot numbers in PLC configuration
3. **Test Connection**: Use the "Test Connection" button in the web interface
4. **Check Firewall**: Ensure port 102 (S7 protocol) is not blocked

### Common Issues

- **"Connection failed"**: Check PLC IP address and network connectivity
- **"IO reading error"**: Verify PLC address format and data type
- **"Configuration not saved"**: Check file permissions for `plc_config.json`
- **"AI not responding"**: Make sure Ollama is running and the model is loaded

### Testing Without PLC

You can test the configuration system without a real PLC:

1. Start the application: `python flask_app.py`
2. Access the web interface at `http://localhost:5001`
3. Go to PLC Configuration and set up your settings
4. The connection test will fail (expected without a real PLC)
5. You can still configure settings and test the web interface
6. Connect a real PLC later to test live communication

## AI Integration

The system uses Ollama with the Gemma3 1B model for local AI processing:

- **Model**: `gemma3:1b` (optimized for Raspberry Pi)
- **API**: Local Ollama server on port 11434
- **Features**: Real-time analysis, operator reports, system health insights

## Requirements

- Python 3.7+
- python-snap7 (for PLC communication)
- Flask (web framework)
- pandas (data processing)
- plotly (visualizations)
- requests (AI API calls)

## Deployment Options

### Windows
```bash
python flask_app.py
```

### Linux/Raspberry Pi
```bash
# Run directly
python3 flask_app.py

# Or use the provided script
chmod +x run.sh
./scripts/run.sh
```

### As a Service (Linux/Raspberry Pi)
```bash
# Copy service file
sudo cp deploy/plc-estop.service /etc/systemd/system/

# Enable and start service
sudo systemctl enable plc-estop.service
sudo systemctl start plc-estop.service
```

## License

This project is open source and available under the MIT License.
