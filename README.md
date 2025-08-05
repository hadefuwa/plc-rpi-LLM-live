# E-Stop AI Status Reporter

A Flask-based web application for monitoring PLC systems and generating intelligent operator reports using AI. The system can read live data from Siemens S7 PLCs and provide real-time analysis and alerts.

## Features

- **Live PLC Communication**: Connect to Siemens S7 PLCs using python-snap7
- **Configurable IO Mapping**: Easy web interface to configure PLC addresses and data types
- **Real-time Monitoring**: Live status updates and system health monitoring
- **AI-Powered Analysis**: Intelligent operator reports using local AI (Gemma3 1B)
- **Interactive Visualizations**: Real-time charts and system status displays
- **Emergency Stop Detection**: Automatic detection and reporting of E-Stop events

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Test the Setup

```bash
python test_plc_setup.py
```

This will test your configuration system and PLC communication setup.

### 3. Start the Application

```bash
python flask_app.py
```

### 4. Access the Web Interface

Open your browser and go to: `http://localhost:5001`

## PLC Configuration

### Setting Up Your PLC

1. **Access Configuration Page**: Click "PLC Configuration" on the main dashboard
2. **Set PLC Connection**: Enter your PLC's IP address, rack, and slot numbers
3. **Configure IO Mapping**: Set up your PLC addresses for each IO point
4. **Test Connection**: Use the "Test Connection" button to verify communication

### Supported PLC Address Formats

- **Bit (DBX)**: `DB1.DBX0.0` - Single bit reading
- **Byte (DBB)**: `DB1.DBB0` - 8-bit reading  
- **Word (DBW)**: `DB1.DBW0` - 16-bit reading
- **DWord (DBD)**: `DB1.DBD0` - 32-bit reading

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
plc-rpi-LLM/
├── flask_app.py          # Main Flask application
├── config.py             # Configuration management
├── plc_communicator.py   # PLC communication class
├── test_plc_setup.py    # Setup testing script
├── plc_config.json      # PLC configuration file (auto-generated)
├── plc_io_data.csv      # Sample CSV data (Phase 1)
├── requirements.txt      # Python dependencies
└── README.md            # This file
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

## Development Phases

### Phase 1: Foundation ✅
- Basic Flask application with CSV data
- Interactive visualizations
- AI integration with Ollama

### Phase 2: PLC Integration ✅
- PLC communication with python-snap7
- Configurable IO mapping system
- Web-based configuration interface
- Connection testing and validation

### Phase 3: Real-time Integration (Next)
- Replace CSV data with live PLC data
- Real-time monitoring and updates
- E-Stop detection and triggering
- Enhanced AI analysis

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

### Testing Without PLC

You can test the configuration system without a real PLC:

1. Run `python test_plc_setup.py`
2. The connection test will fail (expected)
3. You can still configure settings and test the web interface
4. Connect a real PLC later to test live communication

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

## License

This project is open source and available under the MIT License.
