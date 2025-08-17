#!/usr/bin/env python3
"""
Test script for improved PLC polling system
Run this to test the new polling improvements
"""

import time
import sys
import os

# Add current directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from plc_communicator import PLCCommunicator
from event_logger import EventLogger
from config import get_io_mapping

def test_polling_performance():
    """Test the improved polling system"""
    print("=== PLC Polling Performance Test ===\n")
    
    # Initialize components
    plc = PLCCommunicator()
    event_logger = EventLogger()
    io_mapping = get_io_mapping()
    
    print(f"Configured IO points: {len(io_mapping)}")
    print(f"IO mapping keys: {list(io_mapping.keys())[:5]}...")  # Show first 5
    
    # Test connection
    print("\n1. Testing PLC connection...")
    if plc.connect():
        print("✅ PLC connected successfully")
    else:
        print("❌ Failed to connect to PLC")
        return False
    
    # Test bulk read
    print("\n2. Testing bulk read performance...")
    start_time = time.time()
    bulk_results = plc.read_all_io()
    bulk_time = time.time() - start_time
    
    print(f"Bulk read time: {bulk_time:.3f} seconds")
    print(f"Bulk read results: {len(bulk_results)} values")
    
    # Test individual reads for comparison
    print("\n3. Testing individual read performance...")
    start_time = time.time()
    individual_results = {}
    for io_name in list(io_mapping.keys())[:10]:  # Test first 10 only
        try:
            value = plc.read_io(io_name)
            individual_results[io_name] = value
        except Exception as e:
            print(f"Error reading {io_name}: {e}")
    individual_time = time.time() - start_time
    
    print(f"Individual read time (10 points): {individual_time:.3f} seconds")
    print(f"Individual read results: {len(individual_results)} values")
    
    # Calculate performance improvement
    if individual_time > 0:
        improvement = (individual_time / bulk_time) if bulk_time > 0 else 0
        print(f"\nPerformance improvement: {improvement:.1f}x faster with bulk reads")
    
    # Test change detection
    print("\n4. Testing change detection...")
    
    # Simulate some changes
    test_changes = 0
    for i in range(5):
        print(f"  Poll cycle {i+1}...")
        
        # Read current state
        current_data = {}
        for io_name, io_config in io_mapping.items():
            try:
                value = plc.read_io(io_name)
                current_data[io_name] = {
                    'value': value,
                    'type': io_config['type'],
                    'description': io_config['description'],
                    'address': io_config['address'],
                    'status': 'online' if value is not None else 'error'
                }
            except Exception:
                current_data[io_name] = {
                    'value': None,
                    'type': io_config['type'],
                    'description': io_config['description'],
                    'address': io_config['address'],
                    'status': 'error'
                }
        
        # Check for changes
        changes = event_logger.check_and_log_changes(current_data, io_mapping)
        if changes:
            test_changes += len(changes)
            print(f"    Detected {len(changes)} changes")
        else:
            print(f"    No changes detected")
        
        time.sleep(0.1)  # Small delay between polls
    
    print(f"\nTotal changes detected: {test_changes}")
    
    # Cleanup
    plc.disconnect()
    print("\n✅ Test completed successfully")
    return True

def test_adaptive_polling():
    """Test the adaptive polling concept"""
    print("\n=== Adaptive Polling Test ===\n")
    
    # Simulate adaptive polling
    normal_interval = 0.2
    fast_interval = 0.05
    fast_duration = 2.0
    
    current_interval = normal_interval
    last_change_time = 0
    
    print("Simulating adaptive polling behavior:")
    print(f"  Normal interval: {normal_interval}s")
    print(f"  Fast interval: {fast_interval}s")
    print(f"  Fast duration: {fast_duration}s")
    
    for i in range(10):
        current_time = time.time()
        
        # Simulate a change every 3rd cycle
        if i % 3 == 0:
            last_change_time = current_time
            current_interval = fast_interval
            print(f"  Cycle {i+1}: Change detected, switching to fast polling")
        else:
            # Check if we should switch back to normal
            if current_interval == fast_interval:
                time_since_change = current_time - last_change_time
                if time_since_change > fast_duration:
                    current_interval = normal_interval
                    print(f"  Cycle {i+1}: Switching back to normal polling")
                else:
                    print(f"  Cycle {i+1}: Fast polling ({time_since_change:.1f}s since change)")
            else:
                print(f"  Cycle {i+1}: Normal polling")
        
        time.sleep(0.1)  # Simulate work time

if __name__ == "__main__":
    try:
        success = test_polling_performance()
        if success:
            test_adaptive_polling()
        print("\n🎉 All tests completed!")
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
