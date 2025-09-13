"""
PLC Communication Module for E-Stop AI Status Reporter
Handles communication with Siemens S7 PLC using python-snap7
Supports bit, byte, word, and dword data types
"""

import snap7
from snap7.util import *
import time
import logging
from typing import Dict, Any, Optional, Union
from config import get_plc_settings, get_io_mapping

class PLCCommunicator:
    """
    PLC Communication class for Siemens S7 PLC
    Handles connection, reading, and writing of PLC data
    """
    
    def __init__(self):
        """
        Initialize PLC communicator
        
        Args:
            ip: PLC IP address (defaults to config)
            rack: PLC rack number (defaults to config)
            slot: PLC slot number (defaults to config)
        """
        self.client = snap7.client.Client()
        self.connected = False
        self.last_error = ""
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Connection status
        self.connection_time = None
        self.last_read_time = None
        
        # Connection retry settings
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        self.last_connection_attempt = 0
        self.connection_attempt_interval = 5.0  # seconds between connection attempts
        
    def connect(self):
        """Connect to PLC using settings from config with retry logic"""
        try:
            # Don't attempt connection too frequently
            current_time = time.time()
            if (current_time - self.last_connection_attempt) < self.connection_attempt_interval:
                return self.connected
            
            self.last_connection_attempt = current_time
            
            # If already connected, verify connection is still good
            if self.connected and self.client.get_connected():
                return True
            
            settings = get_plc_settings()
            ip = settings.get('ip', '192.168.0.99')
            rack = settings.get('rack', 0)
            slot = settings.get('slot', 1)
            
            print(f"Connecting to PLC at {ip}, rack {rack}, slot {slot}")
            
            # Try to connect with retries
            for attempt in range(self.max_retries):
                try:
                    # Connect to PLC
                    self.client.connect(ip, rack, slot)
                    
                    if self.client.get_connected():
                        self.connected = True
                        self.last_error = ""
                        self.connection_time = current_time
                        print("✅ Successfully connected to PLC")
                        return True
                    else:
                        self.last_error = "Failed to connect to PLC"
                        print(f"❌ {self.last_error} (attempt {attempt + 1}/{self.max_retries})")
                        
                except Exception as e:
                    self.last_error = f"Connection error: {str(e)}"
                    print(f"❌ {self.last_error} (attempt {attempt + 1}/{self.max_retries})")
                
                # Wait before retry (except on last attempt)
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
            
            # All attempts failed
            self.connected = False
            return False
                
        except Exception as e:
            self.last_error = f"Connection error: {str(e)}"
            print(f"❌ {self.last_error}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from PLC"""
        try:
            if self.connected:
                self.client.disconnect()
                self.connected = False
                print("Disconnected from PLC")
        except Exception as e:
            print(f"Error disconnecting: {e}")
    
    def is_connected(self):
        """Check if connected to PLC"""
        return self.connected and self.client.get_connected()
    
    def read_bit(self, db_number, byte_offset, bit_offset):
        """Read a single bit from PLC"""
        try:
            if not self.is_connected():
                return None
                
            # Read one byte from the specified address
            data = self.client.db_read(db_number, byte_offset, 1)
            
            # Extract the specific bit
            bit_value = get_bool(data, 0, bit_offset)
            return bit_value
            
        except Exception as e:
            self.last_error = f"Error reading bit: {str(e)}"
            return None
    
    def read_byte(self, db_number, byte_offset):
        """Read a byte from PLC"""
        try:
            if not self.is_connected():
                return None
                
            data = self.client.db_read(db_number, byte_offset, 1)
            return data[0]  # Return the byte value
            
        except Exception as e:
            self.last_error = f"Error reading byte: {str(e)}"
            return None
    
    def read_word(self, db_number, byte_offset):
        """Read a word (16-bit) from PLC"""
        try:
            if not self.is_connected():
                return None
                
            data = self.client.db_read(db_number, byte_offset, 2)
            return get_int(data, 0)  # Convert 2 bytes to integer
            
        except Exception as e:
            self.last_error = f"Error reading word: {str(e)}"
            return None
    
    def read_dword(self, db_number, byte_offset):
        """Read a dword (32-bit) from PLC"""
        try:
            if not self.is_connected():
                return None
                
            data = self.client.db_read(db_number, byte_offset, 4)
            return get_dword(data, 0)  # Convert 4 bytes to integer
            
        except Exception as e:
            self.last_error = f"Error reading dword: {str(e)}"
            return None
    
    def read_real(self, db_number, byte_offset):
        """Read a real (32-bit IEEE float) from PLC"""
        try:
            if not self.is_connected():
                return None

            data = self.client.db_read(db_number, byte_offset, 4)
            return get_real(data, 0)

        except Exception as e:
            self.last_error = f"Error reading real: {str(e)}"
            return None
    
    def parse_address(self, address):
        """Parse PLC address like 'DB1.DBX0.0' or 'DB1.DBW2'"""
        try:
            # Split address into parts
            parts = address.split('.')
            
            if len(parts) < 2:
                raise ValueError(f"Invalid address format: {address}")
            
            # Extract DB number
            db_part = parts[0]  # DB1
            if not db_part.startswith('DB'):
                raise ValueError(f"Invalid DB format: {db_part}")
            db_number = int(db_part[2:])
            
            # Parse data type and offset
            data_part = parts[1]  # DBX0 or DBW2
            
            if data_part.startswith('DBX'):
                # Bit reading: DBX0.0
                data_type = 'bit'
                byte_offset = int(data_part[3:])
                bit_offset = int(parts[2]) if len(parts) > 2 else 0
                
            elif data_part.startswith('DBB'):
                # Byte reading: DBB0
                data_type = 'byte'
                byte_offset = int(data_part[3:])
                bit_offset = 0
                
            elif data_part.startswith('DBW'):
                # Word reading: DBW2
                data_type = 'word'
                byte_offset = int(data_part[3:])
                bit_offset = 0
                
            elif data_part.startswith('DBD'):
                # DWord reading: DBD4 (can represent unsigned int or real)
                data_type = 'dword'
                byte_offset = int(data_part[3:])
                bit_offset = 0
                
            else:
                raise ValueError(f"Unknown data type in address: {data_part}")
            
            return {
                'db_number': db_number,
                'data_type': data_type,
                'byte_offset': byte_offset,
                'bit_offset': bit_offset
            }
            
        except Exception as e:
            raise ValueError(f"Error parsing address '{address}': {str(e)}")
    
    def read_io(self, io_name):
        """Read a specific IO point by name"""
        try:
            io_mapping = get_io_mapping()
            
            if io_name not in io_mapping:
                raise ValueError(f"IO '{io_name}' not found in mapping")
            
            io_config = io_mapping[io_name]
            address = io_config['address']
            data_type = io_config['type']
            
            # Parse the address
            addr_info = self.parse_address(address)
            
            # Read based on data type
            if data_type == 'bit':
                value = self.read_bit(addr_info['db_number'], 
                                    addr_info['byte_offset'], 
                                    addr_info['bit_offset'])
            elif data_type == 'byte':
                value = self.read_byte(addr_info['db_number'], 
                                     addr_info['byte_offset'])
            elif data_type == 'word':
                value = self.read_word(addr_info['db_number'], 
                                     addr_info['byte_offset'])
            elif data_type == 'dword':
                value = self.read_dword(addr_info['db_number'], 
                                      addr_info['byte_offset'])
            elif data_type == 'real':
                value = self.read_real(addr_info['db_number'],
                                       addr_info['byte_offset'])
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
            
            return value
            
        except Exception as e:
            self.last_error = f"Error reading IO '{io_name}': {str(e)}"
            return None
    
    def read_all_io(self):
        """Read all configured IO points using a single bulk DB read per DB number.
        Handles DB size limits and falls back gracefully to individual reads.
        """
        try:
            if not self.is_connected():
                return {}
                
            io_mapping = get_io_mapping()
            if not io_mapping:
                return {}
            
            # Group addresses by DB
            db_to_offsets: Dict[int, int] = {}
            parsed: Dict[str, Dict[str, int]] = {}
            
            for name, cfg in io_mapping.items():
                try:
                    info = self.parse_address(cfg['address'])
                    parsed[name] = info
                    
                    # Calculate end offset based on data type
                    if cfg['type'] == 'bit':
                        end_offset = info['byte_offset'] + 1
                    elif cfg['type'] in ('dword', 'real'):
                        end_offset = info['byte_offset'] + 4
                    elif cfg['type'] == 'word':
                        end_offset = info['byte_offset'] + 2
                    else:  # byte
                        end_offset = info['byte_offset'] + 1
                        
                    db_to_offsets[info['db_number']] = max(
                        db_to_offsets.get(info['db_number'], 0), 
                        end_offset
                    )
                except Exception as e:
                    print(f"Error parsing address for {name}: {e}")
                    continue

            # Read buffers per DB with conservative approach
            db_buffers: Dict[int, bytes] = {}
            for db_num, size in db_to_offsets.items():
                if size <= 0:
                    continue
                    
                # Conservative read size - don't add extra margin
                read_size = size
                
                # Try smaller chunks if the full read fails
                chunk_sizes = [read_size, read_size // 2, read_size // 4, 64, 32, 16]
                
                for chunk_size in chunk_sizes:
                    if chunk_size <= 0:
                        continue
                        
                    try:
                        print(f"Trying to read DB{db_num} from offset 0, size {chunk_size}")
                        db_buffers[db_num] = self.client.db_read(db_num, 0, chunk_size)
                        if db_buffers[db_num] is not None:
                            print(f"Successfully read DB{db_num} with size {chunk_size}")
                            break
                    except Exception as e:
                        print(f"Failed to read DB{db_num} with size {chunk_size}: {e}")
                        continue
                else:
                    # All chunk sizes failed
                    print(f"All read attempts failed for DB{db_num}")
                    db_buffers[db_num] = None

            # Decode values from buffers
            results: Dict[str, Any] = {}
            for name, cfg in io_mapping.items():
                if name not in parsed:
                    results[name] = None
                    continue
                    
                info = parsed[name]
                buf = db_buffers.get(info['db_number'])
                
                if not buf:
                    results[name] = None
                    continue
                    
                # Check if we have enough data in the buffer
                required_size = info['byte_offset']
                if cfg['type'] in ('dword', 'real'):
                    required_size += 4
                elif cfg['type'] == 'word':
                    required_size += 2
                else:  # bit or byte
                    required_size += 1
                    
                if len(buf) < required_size:
                    print(f"Buffer too small for {name}: need {required_size}, have {len(buf)}")
                    results[name] = None
                    continue
                    
                try:
                    if cfg['type'] == 'bit':
                        results[name] = get_bool(buf, info['byte_offset'], info['bit_offset'])
                    elif cfg['type'] == 'byte':
                        results[name] = buf[info['byte_offset']]
                    elif cfg['type'] == 'word':
                        results[name] = get_int(bytearray(buf[info['byte_offset']:info['byte_offset']+2]), 0)
                    elif cfg['type'] == 'dword':
                        results[name] = get_dword(bytearray(buf[info['byte_offset']:info['byte_offset']+4]), 0)
                    elif cfg['type'] == 'real':
                        results[name] = get_real(bytearray(buf[info['byte_offset']:info['byte_offset']+4]), 0)
                    else:
                        results[name] = None
                        
                except Exception as e:
                    print(f"Error decoding {name} from buffer: {e}")
                    results[name] = None

            return results

        except Exception as e:
            self.last_error = f"Error reading all IO (bulk): {str(e)}"
            print(f"Bulk read failed: {e}")
            return {}
    
    def test_connection(self):
        """Test PLC connection and basic communication"""
        try:
            if not self.connect():
                return False, "Failed to connect to PLC"
            
            # Try to read a small amount of data to test communication
            test_data = self.client.db_read(1, 0, 1)
            
            if test_data is not None:
                return True, "Connection test successful"
            else:
                return False, "Could not read data from PLC"
                
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
        finally:
            self.disconnect()
    
    def get_status(self):
        """Get current PLC connection status"""
        return {
            'connected': self.is_connected(),
            'last_error': self.last_error,
            'plc_settings': get_plc_settings(),
            'io_count': len(get_io_mapping())
        }

# Example usage and testing
if __name__ == "__main__":
    plc = PLCCommunicator()
    
    print("Testing PLC connection...")
    success, message = plc.test_connection()
    print(f"Test result: {message}")
    
    if success:
        print("\nTesting IO reading...")
        plc.connect()
        
        # Read all configured IO
        io_data = plc.read_all_io()
        print("IO Data:")
        for name, value in io_data.items():
            print(f"  {name}: {value}")
        
        plc.disconnect()
    else:
        print("Cannot test IO reading without connection") 