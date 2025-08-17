#!/usr/bin/env python3
"""
Real-time PLC polling monitor
Run this to see the improved polling system in action
"""

import time
import sys
import os
from datetime import datetime

# Add current directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from plc_communicator import PLCCommunicator
from event_logger import EventLogger
from config import get_io_mapping

def monitor_polling():
    """Monitor the PLC polling in real-time"""
    print("=== Real-Time PLC Polling Monitor ===\n")
    print("Press Ctrl+C to stop monitoring\n")
    
    # Initialize components
    plc = PLCCommunicator()
    event_logger = EventLogger()
    io_mapping = get_io_mapping()
    
    # Connection test
    if not plc.connect():
        print("❌ Failed to connect to PLC")
        return
    
    print("✅ Connected to PLC")
    print(f"📊 Monitoring {len(io_mapping)} IO points")
    print("=" * 60)
    
    # Monitoring variables
    poll_count = 0
    change_count = 0
    last_report_time = time.time()
    report_interval = 5.0  # Report every 5 seconds
    
    try:
        while True:
            poll_start = time.time()
            poll_count += 1
            
            # Read all IO using bulk method
            bulk_start = time.time()
            bulk_results = plc.read_all_io()
            bulk_time = time.time() - bulk_start
            
            # Convert to expected format
            current_data = {}
            for io_name, io_config in io_mapping.items():
                value = bulk_results.get(io_name)
                current_data[io_name] = {
                    'value': value,
                    'type': io_config['type'],
                    'description': io_config['description'],
                    'address': io_config['address'],
                    'status': 'online' if value is not None else 'error'
                }
            
            # Check for changes
            changes = event_logger.check_and_log_changes(current_data, io_mapping)
            if changes:
                change_count += len(changes)
                print(f"\n🔄 {datetime.now().strftime('%H:%M:%S')} - Detected {len(changes)} changes:")
                for change in changes[:3]:  # Show first 3 changes
                    io_name = change.get('io_name', 'Unknown')
                    old_val = change.get('old_value')
                    new_val = change.get('new_value')
                    print(f"   {io_name}: {old_val} → {new_val}")
                if len(changes) > 3:
                    print(f"   ... and {len(changes) - 3} more changes")
            
            total_time = time.time() - poll_start
            
            # Periodic status report
            current_time = time.time()
            if current_time - last_report_time >= report_interval:
                print(f"\n📈 Status Report ({datetime.now().strftime('%H:%M:%S')}):")
                print(f"   Polls: {poll_count}")
                print(f"   Changes: {change_count}")
                print(f"   Avg poll time: {total_time:.3f}s")
                print(f"   Bulk read time: {bulk_time:.3f}s")
                print(f"   Change rate: {change_count/poll_count:.2f} changes/poll")
                
                # Show some current values
                print(f"   Sample values:")
                sample_count = 0
                for io_name, info in current_data.items():
                    if sample_count < 5:  # Show first 5
                        value = info.get('value')
                        status = info.get('status')
                        print(f"     {io_name}: {value} ({status})")
                        sample_count += 1
                
                print("-" * 40)
                last_report_time = current_time
            
            # Small delay to prevent overwhelming the PLC
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print(f"\n\n📊 Final Statistics:")
        print(f"   Total polls: {poll_count}")
        print(f"   Total changes: {change_count}")
        print(f"   Average change rate: {change_count/poll_count:.2f} changes/poll")
        print("\n👋 Monitoring stopped")
    
    finally:
        plc.disconnect()

def monitor_specific_io():
    """Monitor specific IO points that are likely to change"""
    print("=== Specific IO Monitor ===\n")
    
    # Initialize components
    plc = PLCCommunicator()
    event_logger = EventLogger()
    io_mapping = get_io_mapping()
    
    # Find button-related IO points
    button_ios = []
    for io_name, io_config in io_mapping.items():
        if any(keyword in io_name.lower() for keyword in ['button', 'switch', 'estop']):
            button_ios.append(io_name)
    
    print(f"🔍 Monitoring {len(button_ios)} button/switch IO points:")
    for io_name in button_ios:
        print(f"   - {io_name}")
    
    if not plc.connect():
        print("❌ Failed to connect to PLC")
        return
    
    print("\nPress Ctrl+C to stop monitoring\n")
    print("=" * 60)
    
    try:
        while True:
            # Read only button IO points
            button_values = {}
            for io_name in button_ios:
                try:
                    value = plc.read_io(io_name)
                    button_values[io_name] = value
                except Exception as e:
                    button_values[io_name] = None
            
            # Display current button states
            print(f"\r{datetime.now().strftime('%H:%M:%S')} - ", end="")
            for io_name, value in button_values.items():
                status = "ON" if value else "OFF"
                print(f"{io_name}: {status} | ", end="")
            
            time.sleep(0.05)  # 50ms polling for buttons
            
    except KeyboardInterrupt:
        print("\n\n👋 Button monitoring stopped")
    
    finally:
        plc.disconnect()

if __name__ == "__main__":
    print("Choose monitoring mode:")
    print("1. Full system monitoring")
    print("2. Button/switch monitoring only")
    
    try:
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == "1":
            monitor_polling()
        elif choice == "2":
            monitor_specific_io()
        else:
            print("Invalid choice, running full monitoring...")
            monitor_polling()
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
