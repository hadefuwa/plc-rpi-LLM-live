#!/usr/bin/env python3
"""
PLC Diagnostic Script
Run this to diagnose PLC connection and DB size issues
"""

import time
import sys
import os

# Add current directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from plc_communicator import PLCCommunicator
from config import get_io_mapping, get_plc_settings

def diagnose_plc():
    """Diagnose PLC connection and DB issues"""
    print("=== PLC Diagnostic Tool ===\n")
    
    # Get PLC settings
    settings = get_plc_settings()
    print(f"PLC Settings:")
    print(f"  IP: {settings.get('ip', 'Not set')}")
    print(f"  Rack: {settings.get('rack', 'Not set')}")
    print(f"  Slot: {settings.get('slot', 'Not set')}")
    
    # Get IO mapping
    io_mapping = get_io_mapping()
    print(f"\nIO Configuration:")
    print(f"  Total IO points: {len(io_mapping)}")
    
    # Analyze DB usage
    db_usage = {}
    for name, cfg in io_mapping.items():
        try:
            address = cfg['address']
            if address.startswith('DB'):
                parts = address.split('.')
                if len(parts) >= 2:
                    db_part = parts[0]  # DB1
                    db_num = int(db_part[2:])
                    
                    if db_num not in db_usage:
                        db_usage[db_num] = {'min_offset': 999999, 'max_offset': 0, 'count': 0}
                    
                    # Parse offset
                    data_part = parts[1]  # DBX0 or DBW2
                    if data_part.startswith('DBX'):
                        offset = int(data_part[3:])
                    elif data_part.startswith('DBB'):
                        offset = int(data_part[3:])
                    elif data_part.startswith('DBW'):
                        offset = int(data_part[3:])
                    elif data_part.startswith('DBD'):
                        offset = int(data_part[3:])
                    else:
                        continue
                    
                    db_usage[db_num]['min_offset'] = min(db_usage[db_num]['min_offset'], offset)
                    db_usage[db_num]['max_offset'] = max(db_usage[db_num]['max_offset'], offset)
                    db_usage[db_num]['count'] += 1
                    
        except Exception as e:
            print(f"Error parsing {name}: {e}")
    
    print(f"\nDB Usage Analysis:")
    for db_num, usage in db_usage.items():
        print(f"  DB{db_num}: {usage['count']} points, offset range {usage['min_offset']}-{usage['max_offset']}")
    
    # Test connection
    print(f"\nTesting PLC Connection...")
    plc = PLCCommunicator()
    
    if plc.connect():
        print("✅ PLC connected successfully")
        
        # Test individual reads first
        print(f"\nTesting individual reads...")
        success_count = 0
        error_count = 0
        
        for name, cfg in list(io_mapping.items())[:10]:  # Test first 10
            try:
                value = plc.read_io(name)
                if value is not None:
                    success_count += 1
                    print(f"  ✅ {name}: {value}")
                else:
                    error_count += 1
                    print(f"  ❌ {name}: Failed to read")
            except Exception as e:
                error_count += 1
                print(f"  ❌ {name}: {e}")
        
        print(f"\nIndividual read results: {success_count} success, {error_count} errors")
        
        # Test bulk read
        print(f"\nTesting bulk read...")
        try:
            bulk_results = plc.read_all_io()
            if bulk_results:
                print(f"✅ Bulk read successful: {len(bulk_results)} values")
                # Show first few results
                for name, value in list(bulk_results.items())[:5]:
                    print(f"  {name}: {value}")
            else:
                print("❌ Bulk read returned no data")
        except Exception as e:
            print(f"❌ Bulk read failed: {e}")
        
        # Test DB size limits
        print(f"\nTesting DB size limits...")
        for db_num in db_usage.keys():
            test_sizes = [16, 32, 64, 128, 256, 512, 1024]
            for size in test_sizes:
                try:
                    print(f"  Testing DB{db_num} size {size}...")
                    data = plc.client.db_read(db_num, 0, size)
                    if data is not None:
                        print(f"    ✅ DB{db_num} supports size {size}")
                    else:
                        print(f"    ❌ DB{db_num} failed at size {size}")
                        break
                except Exception as e:
                    print(f"    ❌ DB{db_num} failed at size {size}: {e}")
                    break
        
        plc.disconnect()
        
    else:
        print("❌ Failed to connect to PLC")
        print(f"Error: {plc.last_error}")

def test_specific_addresses():
    """Test specific addresses that might be causing issues"""
    print("\n=== Testing Specific Addresses ===\n")
    
    plc = PLCCommunicator()
    if not plc.connect():
        print("❌ Cannot connect to PLC")
        return
    
    # Test some common problematic addresses
    test_addresses = [
        ("DB1.DBX0.0", "bit"),
        ("DB1.DBX0.1", "bit"),
        ("DB1.DBW2", "word"),
        ("DB1.DBW28", "word"),
        ("DB1.DBD30", "real"),
    ]
    
    for address, data_type in test_addresses:
        try:
            print(f"Testing {address} ({data_type})...")
            
            # Parse address
            info = plc.parse_address(address)
            print(f"  Parsed: DB{info['db_number']}, offset {info['byte_offset']}, bit {info['bit_offset']}")
            
            # Try to read
            if data_type == 'bit':
                value = plc.read_bit(info['db_number'], info['byte_offset'], info['bit_offset'])
            elif data_type == 'word':
                value = plc.read_word(info['db_number'], info['byte_offset'])
            elif data_type == 'real':
                value = plc.read_real(info['db_number'], info['byte_offset'])
            else:
                value = None
            
            if value is not None:
                print(f"  ✅ Success: {value}")
            else:
                print(f"  ❌ Failed to read")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    plc.disconnect()

if __name__ == "__main__":
    try:
        diagnose_plc()
        test_specific_addresses()
        print("\n🎉 Diagnosis complete!")
    except KeyboardInterrupt:
        print("\n\n⚠️  Diagnosis interrupted by user")
    except Exception as e:
        print(f"\n❌ Diagnosis failed: {e}")
        import traceback
        traceback.print_exc()
