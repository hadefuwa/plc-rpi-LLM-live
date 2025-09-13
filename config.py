"""
Configuration file for E-Stop AI Status Reporter
Contains PLC connection settings, IO mapping, and AI prompt templates
"""

import json
import os

# Default AI reporting configuration
DEFAULT_AI_CONFIG = {
    "report_interval_minutes": 15,
    "startup_delay_seconds": 30,
    "max_events_for_analysis": 100,
    "system_prompt": """You are an industrial automation AI assistant tasked with producing a comprehensive report on what has occurred on this PLC test machine during the last {interval_minutes} minutes.

SYSTEM CONTEXT:
- This is a Siemens S7-1200 PLC controlling a test rig with safety systems
- Emergency stop functionality is present and critical for safety
- System includes: buttons, switches, LEDs, analog inputs, and spare I/O
- Forced values indicate manual overrides that may mask true process states

CURRENT IO DATA:
{data_context}

RECENT EVENTS (Last {interval_minutes} minutes - {event_count} total):
{recent_events}

ANALYSIS REQUIREMENTS:
1. SAFETY STATUS: Report on emergency stop status and any safety-related events
2. OPERATIONAL CHANGES: Identify what operations or tests were performed
3. SYSTEM HEALTH: Note any errors, forced values, or unusual conditions
4. TREND ANALYSIS: Describe patterns in the recent activity
5. RECOMMENDATIONS: Suggest any actions needed (maintenance, investigation, etc.)

Please provide a clear, professional operator report focusing on:
- What actually happened during this period
- Current system status and safety condition
- Any anomalies or items requiring attention
- Operational insights for the test rig

Keep the report concise but comprehensive (5-8 sentences). Focus on actionable insights."""
}

# Default PLC configuration
DEFAULT_CONFIG = {
    "plc": {
        "ip": "192.168.0.99",
        "rack": 0,
        "slot": 1
    },
    "io_mapping": {
        "E_Stop_Status": {
            "type": "bit",
            "address": "DB1.DBX0.0",
            "description": "Emergency stop activation (0=OFF, 1=ON)"
        },
        "Pump_Running": {
            "type": "bit", 
            "address": "DB1.DBX0.1",
            "description": "Pump operational status (0=OFF, 1=ON)"
        },
        "Tank_Level_Low": {
            "type": "bit",
            "address": "DB1.DBX0.2", 
            "description": "Low tank level indicator (0=OK, 1=LOW)"
        },
        "Valve_Open": {
            "type": "bit",
            "address": "DB1.DBX0.3",
            "description": "Valve position (0=CLOSED, 1=OPEN)"
        },
        "Motor_Control": {
            "type": "bit",
            "address": "DB1.DBX0.4",
            "description": "Motor control signal (0=OFF, 1=ON)"
        },
        "Alarm_Relay": {
            "type": "bit",
            "address": "DB1.DBX0.5",
            "description": "Alarm relay status (0=OFF, 1=ON)"
        },
        "Pressure_High": {
            "type": "bit",
            "address": "DB1.DBX0.6",
            "description": "High pressure indicator (0=OK, 1=HIGH)"
        },
        "Temperature_High": {
            "type": "bit",
            "address": "DB1.DBX0.7",
            "description": "High temperature indicator (0=OK, 1=HIGH)"
        },
        "Flow_Rate": {
            "type": "word",
            "address": "DB1.DBW1",
            "description": "System flow rate in L/min"
        }
    },
    "io_groups": {}
}

# Store config under data/plc_config.json
BASE_DIR = os.path.dirname(__file__)
CONFIG_FILE = os.path.join(BASE_DIR, 'data', 'plc_config.json')

def load_config():
    """Load configuration from file, create default if not exists"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            print(f"Error reading {CONFIG_FILE}, using default config")
            return DEFAULT_CONFIG
    else:
        # Create default config file
        # Ensure data directory exists
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

def save_config(config):
    """Save configuration to file"""
    try:
        # Ensure data directory exists
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def get_plc_settings():
    """Get PLC connection settings"""
    config = load_config()
    return config.get("plc", {})

def get_io_mapping():
    """Get IO mapping configuration"""
    config = load_config()
    return config.get("io_mapping", {})

def get_io_groups():
    """Get IO groups configuration"""
    config = load_config()
    return config.get("io_groups", {})

def update_io_group(group_name, io_names_list):
    """Create or update an IO group with a list of IO names"""
    if not isinstance(io_names_list, list):
        raise ValueError("io_names_list must be a list of IO names")
    config = load_config()
    if "io_groups" not in config:
        config["io_groups"] = {}
    config["io_groups"][group_name] = io_names_list
    return save_config(config)

def remove_io_group(group_name):
    """Remove an IO group by name"""
    config = load_config()
    if "io_groups" in config and group_name in config["io_groups"]:
        del config["io_groups"][group_name]
        return save_config(config)
    return True

def update_plc_settings(ip, rack=0, slot=1):
    """Update PLC connection settings"""
    config = load_config()
    config["plc"] = {
        "ip": ip,
        "rack": rack,
        "slot": slot
    }
    return save_config(config)

def update_io_mapping(io_name, io_type, address, description=""):
    """Update a single IO mapping"""
    config = load_config()
    config["io_mapping"][io_name] = {
        "type": io_type,
        "address": address,
        "description": description
    }
    return save_config(config)

def get_config_summary():
    """Get a summary of current configuration"""
    config = load_config()
    plc = config.get("plc", {})
    io_count = len(config.get("io_mapping", {}))
    
    return {
        "plc_ip": plc.get("ip", "Not set"),
        "plc_rack": plc.get("rack", 0),
        "plc_slot": plc.get("slot", 1),
        "io_count": io_count,
        "io_mapping": config.get("io_mapping", {})
    }

# ============================================================
# AI CONFIGURATION FUNCTIONS
# ============================================================

def get_ai_config():
    """Get current AI reporting configuration"""
    ai_config_file = os.path.join(os.path.dirname(__file__), 'ai_config.json')
    try:
        if os.path.exists(ai_config_file):
            with open(ai_config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                merged_config = DEFAULT_AI_CONFIG.copy()
                merged_config.update(config)
                return merged_config
        else:
            return DEFAULT_AI_CONFIG.copy()
    except Exception as e:
        print(f"Error loading AI config: {e}")
        return DEFAULT_AI_CONFIG.copy()

def save_ai_config(config):
    """Save AI reporting configuration"""
    ai_config_file = os.path.join(os.path.dirname(__file__), 'ai_config.json')
    try:
        with open(ai_config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving AI config: {e}")
        return False

def update_ai_report_interval(minutes):
    """Update AI report interval in minutes"""
    config = get_ai_config()
    config["report_interval_minutes"] = int(minutes)
    return save_ai_config(config)

def update_ai_system_prompt(prompt):
    """Update AI system prompt template"""
    config = get_ai_config()
    config["system_prompt"] = prompt
    return save_ai_config(config)

def update_ai_settings(report_interval_minutes=None, startup_delay_seconds=None, 
                      max_events_for_analysis=None, system_prompt=None):
    """Update multiple AI settings at once"""
    config = get_ai_config()
    
    if report_interval_minutes is not None:
        config["report_interval_minutes"] = int(report_interval_minutes)
    if startup_delay_seconds is not None:
        config["startup_delay_seconds"] = int(startup_delay_seconds)
    if max_events_for_analysis is not None:
        config["max_events_for_analysis"] = int(max_events_for_analysis)
    if system_prompt is not None:
        config["system_prompt"] = system_prompt
    
    return save_ai_config(config) 