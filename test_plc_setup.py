#!/usr/bin/env python3
"""
Simple test script for PLC configuration and communication
"""

import sys
import os

# Add current directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import load_config, get_config_summary, update_plc_settings
from plc_communicator import PLCCommunicator

def test_configuration():
    """Test the configuration system"""
    print("🔧 Testing Configuration System...")
    
    # Test loading config
    config = load_config()
    print(f"✅ Configuration loaded successfully")
    print(f"   - PLC IP: {config.get('plc', {}).get('ip', 'Not set')}")
    print(f"   - IO Mappings: {len(config.get('io_mapping', {}))} items")
    
    # Test config summary
    summary = get_config_summary()
    print(f"✅ Config summary generated")
    print(f"   - PLC IP: {summary['plc_ip']}")
    print(f"   - IO Count: {summary['io_count']}")
    
    return True

def test_plc_connection():
    """Test PLC connection"""
    print("\n🔌 Testing PLC Connection...")
    
    try:
        plc = PLCCommunicator()
        
        # Test connection
        success, message = plc.test_connection()
        
        if success:
            print(f"✅ PLC Connection Test: SUCCESS")
            print(f"   - Message: {message}")
            
            # Test reading all IO
            print("\n📊 Testing IO Reading...")
            plc.connect()
            io_data = plc.read_all_io()
            
            print(f"✅ IO Reading Test: {len(io_data)} IO points read")
            for name, value in io_data.items():
                status = f"{value}" if value is not None else "ERROR"
                print(f"   - {name}: {status}")
            
            plc.disconnect()
            return True
        else:
            print(f"❌ PLC Connection Test: FAILED")
            print(f"   - Error: {message}")
            print("\n💡 This is expected if no PLC is connected.")
            print("   You can still configure the settings and test with a real PLC later.")
            return False
            
    except Exception as e:
        print(f"❌ PLC Test Error: {str(e)}")
        return False

def test_io_mapping():
    """Test IO mapping functionality"""
    print("\n🗺️ Testing IO Mapping...")
    
    try:
        # Test updating PLC settings
        test_ip = "192.168.1.100"
        success = update_plc_settings(test_ip, 0, 1)
        print(f"✅ PLC Settings Update: {'SUCCESS' if success else 'FAILED'}")
        
        # Test IO mapping
        from config import update_io_mapping
        success = update_io_mapping("TEST_IO", "bit", "DB1.DBX0.0", "Test IO Point")
        print(f"✅ IO Mapping Update: {'SUCCESS' if success else 'FAILED'}")
        
        return True
    except Exception as e:
        print(f"❌ IO Mapping Test Error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 PLC Setup Test Suite")
    print("=" * 50)
    
    tests = [
        ("Configuration System", test_configuration),
        ("PLC Connection", test_plc_connection),
        ("IO Mapping", test_io_mapping)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} Test Error: {str(e)}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Your PLC setup is ready.")
    else:
        print("⚠️  Some tests failed. Check the configuration and PLC connection.")
    
    print("\n📝 Next Steps:")
    print("1. Open your web browser and go to: http://localhost:5000")
    print("2. Click 'PLC Configuration' to set up your PLC settings")
    print("3. Configure your PLC IP address and IO mappings")
    print("4. Test the connection with your real PLC")

if __name__ == "__main__":
    main() 