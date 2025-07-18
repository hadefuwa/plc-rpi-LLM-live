"""
Configuration file for E-Stop AI Status Reporter
Contains PLC connection settings, IO mapping, and AI prompt templates
"""

# PLC Connection Configuration
PLC_CONFIG = {
    'ip': '192.168.1.100',  # PLC IP address
    'rack': 0,              # PLC rack number
    'slot': 1,              # PLC slot number
    'timeout': 5000,        # Connection timeout in ms
    'retry_attempts': 3,    # Number of retry attempts
    'polling_interval': 1.0  # Polling interval in seconds
}

# IO Mapping Configuration
# Supports: bit (DBX), byte (DBB), word (DBW), dword (DBD)
IO_MAPPING = {
    'emergency_stop': {
        'type': 'bit',
        'address': 'DB1.DBX0.0',
        'description': 'Emergency Stop Button',
        'unit': 'ON/OFF'
    },
    'pump_running': {
        'type': 'bit', 
        'address': 'DB1.DBX0.1',
        'description': 'Pump Running Status',
        'unit': 'ON/OFF'
    },
    'tank_level_low': {
        'type': 'bit',
        'address': 'DB1.DBX0.2', 
        'description': 'Tank Level Low Indicator',
        'unit': 'ON/OFF'
    },
    'valve_open': {
        'type': 'bit',
        'address': 'DB1.DBX0.3',
        'description': 'Valve Open Status',
        'unit': 'ON/OFF'
    },
    'motor_control': {
        'type': 'bit',
        'address': 'DB1.DBX0.4',
        'description': 'Motor Control Signal',
        'unit': 'ON/OFF'
    },
    'alarm_relay': {
        'type': 'bit',
        'address': 'DB1.DBX0.5',
        'description': 'Alarm Relay Status',
        'unit': 'ON/OFF'
    },
    'pressure_high': {
        'type': 'bit',
        'address': 'DB1.DBX0.6',
        'description': 'High Pressure Indicator',
        'unit': 'ON/OFF'
    },
    'temperature_high': {
        'type': 'bit',
        'address': 'DB1.DBX0.7',
        'description': 'High Temperature Indicator',
        'unit': 'ON/OFF'
    },
    'flow_rate': {
        'type': 'word',
        'address': 'DB1.DBW2',
        'description': 'System Flow Rate',
        'unit': 'L/min',
        'scale_factor': 0.1  # Raw value * 0.1 = actual flow rate
    },
    'pressure_value': {
        'type': 'word',
        'address': 'DB1.DBW4',
        'description': 'Pressure Sensor Value',
        'unit': 'bar',
        'scale_factor': 0.01  # Raw value * 0.01 = actual pressure
    },
    'temperature_value': {
        'type': 'word',
        'address': 'DB1.DBW6',
        'description': 'Temperature Sensor Value',
        'unit': '°C',
        'scale_factor': 0.1  # Raw value * 0.1 = actual temperature
    },
    'tank_level_percent': {
        'type': 'word',
        'address': 'DB1.DBW8',
        'description': 'Tank Level Percentage',
        'unit': '%',
        'scale_factor': 0.1  # Raw value * 0.1 = actual percentage
    }
}

# AI Configuration
AI_CONFIG = {
    'model': 'phi3:mini',           # Ollama model to use
    'api_url': 'http://localhost:11434/api/generate',
    'max_tokens': 150,              # Maximum response length
    'temperature': 0.1,             # Response creativity (0.0 = focused, 1.0 = creative)
    'timeout': 30                   # AI request timeout in seconds
}

# AI Prompt Templates
PROMPT_TEMPLATES = {
    'emergency_stop': """
Emergency stop activated at {timestamp}.

Current system status:
{io_summary}

Please generate a concise operator report (2-3 sentences) including:
1. Current system status and what triggered the emergency stop
2. Immediate safety concerns that need attention
3. Recommended immediate actions for the operator

Focus on safety and clear, actionable guidance.
""",

    'system_health': """
System health check at {timestamp}.

Current IO state:
{io_summary}

Analyze the system health and provide insights on:
1. Overall system status and operational condition
2. Any potential issues or warning signs
3. Maintenance or operational recommendations

Be concise and focus on actionable insights.
""",

    'status_query': """
System status query at {timestamp}.

Current system data:
{io_summary}

User question: {user_question}

Please provide a clear, concise answer based on the current system status.
Focus on practical insights and actionable information.
"""
}

# Web Interface Configuration
WEB_CONFIG = {
    'host': '0.0.0.0',              # Listen on all interfaces
    'port': 5000,                   # Web server port
    'debug': False,                 # Debug mode (set to True for development)
    'refresh_interval': 5000,       # Auto-refresh interval in milliseconds
    'max_history': 1000             # Maximum number of events to keep in memory
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': 'INFO',                # Logging level (DEBUG, INFO, WARNING, ERROR)
    'file': 'plc_monitor.log',      # Log file name
    'max_size': 10 * 1024 * 1024,  # Max log file size (10MB)
    'backup_count': 5               # Number of backup log files
}

# E-Stop Detection Configuration
ESTOP_CONFIG = {
    'polling_interval': 0.5,        # E-Stop polling interval in seconds
    'debounce_time': 0.1,           # Debounce time in seconds
    'edge_detection': True,         # Enable edge detection (OFF → ON)
    'auto_reset': False,            # Auto-reset after E-Stop (not recommended for safety)
    'reset_delay': 5.0              # Delay before allowing reset in seconds
}

# Data Storage Configuration
STORAGE_CONFIG = {
    'csv_file': 'plc_io_data.csv',  # CSV file for static data (Phase 1)
    'database_file': 'plc_events.db', # SQLite database for events (Phase 2+)
    'backup_enabled': True,         # Enable automatic backups
    'backup_interval': 3600,        # Backup interval in seconds (1 hour)
    'retention_days': 30            # Keep data for 30 days
}

def get_io_address_info(address):
    """
    Parse PLC address and return address information
    
    Args:
        address (str): PLC address (e.g., 'DB1.DBX0.0', 'DB1.DBW2')
    
    Returns:
        dict: Parsed address information
    """
    try:
        # Parse address format: DB{db_number}.DB{type}{byte_offset}.{bit_offset}
        parts = address.split('.')
        db_part = parts[0]  # DB1
        db_number = int(db_part[2:])
        
        if len(parts) == 2:
            # Word/DWord/Byte format: DB1.DBW2
            data_part = parts[1]  # DBW2
            data_type = data_part[:3]  # DBW
            byte_offset = int(data_part[3:])
            bit_offset = 0
        elif len(parts) == 3:
            # Bit format: DB1.DBX0.0
            data_part = parts[1]  # DBX0
            bit_part = parts[2]   # 0
            data_type = data_part[:3]  # DBX
            byte_offset = int(data_part[3:])
            bit_offset = int(bit_part)
        else:
            raise ValueError(f"Invalid address format: {address}")
        
        return {
            'db_number': db_number,
            'data_type': data_type,
            'byte_offset': byte_offset,
            'bit_offset': bit_offset,
            'original_address': address
        }
    except Exception as e:
        raise ValueError(f"Error parsing address '{address}': {str(e)}")

def validate_config():
    """
    Validate configuration settings
    
    Returns:
        list: List of validation errors (empty if valid)
    """
    errors = []
    
    # Validate PLC config
    if not PLC_CONFIG['ip'] or PLC_CONFIG['ip'] == '192.168.1.100':
        errors.append("PLC IP address not configured")
    
    # Validate IO mapping
    for name, config in IO_MAPPING.items():
        try:
            get_io_address_info(config['address'])
        except ValueError as e:
            errors.append(f"Invalid IO address for '{name}': {e}")
    
    # Validate AI config
    if AI_CONFIG['temperature'] < 0 or AI_CONFIG['temperature'] > 1:
        errors.append("AI temperature must be between 0 and 1")
    
    return errors

if __name__ == "__main__":
    # Test configuration
    print("Configuration Validation:")
    errors = validate_config()
    if errors:
        print("❌ Configuration errors found:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ Configuration is valid")
    
    print(f"\nIO Mapping ({len(IO_MAPPING)} items):")
    for name, config in IO_MAPPING.items():
        print(f"  {name}: {config['address']} ({config['type']}) - {config['description']}") 