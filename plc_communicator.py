"""
PLC Communication Module for E-Stop AI Status Reporter
Handles communication with Siemens S7 PLC using python-snap7
Supports bit, byte, word, and dword data types
"""

import snap7
import time
import logging
from typing import Dict, Any, Optional, Union
from config import PLC_CONFIG, IO_MAPPING, get_io_address_info

class PLCCommunicator:
    """
    PLC Communication class for Siemens S7 PLC
    Handles connection, reading, and writing of PLC data
    """
    
    def __init__(self, ip: str = None, rack: int = None, slot: int = None):
        """
        Initialize PLC communicator
        
        Args:
            ip: PLC IP address (defaults to config)
            rack: PLC rack number (defaults to config)
            slot: PLC slot number (defaults to config)
        """
        self.ip = ip or PLC_CONFIG['ip']
        self.rack = rack or PLC_CONFIG['rack']
        self.slot = slot or PLC_CONFIG['slot']
        self.timeout = PLC_CONFIG['timeout']
        self.retry_attempts = PLC_CONFIG['retry_attempts']
        
        # Initialize snap7 client
        self.client = snap7.client.Client()
        self.connected = False
        self.last_error = None
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Connection status
        self.connection_time = None
        self.last_read_time = None
        
    def connect(self) -> bool:
        """
        Connect to PLC
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.logger.info(f"Connecting to PLC at {self.ip}:{self.rack}/{self.slot}")
            
            # Connect to PLC
            result = self.client.connect(self.ip, self.rack, self.slot)
            
            if result == 0:
                self.connected = True
                self.connection_time = time.time()
                self.last_error = None
                self.logger.info("Successfully connected to PLC")
                return True
            else:
                self.connected = False
                self.last_error = f"Connection failed with result code: {result}"
                self.logger.error(self.last_error)
                return False
                
        except Exception as e:
            self.connected = False
            self.last_error = str(e)
            self.logger.error(f"Connection error: {self.last_error}")
            return False
    
    def disconnect(self):
        """Disconnect from PLC"""
        if self.connected:
            try:
                self.client.disconnect()
                self.connected = False
                self.logger.info("Disconnected from PLC")
            except Exception as e:
                self.logger.error(f"Error disconnecting: {e}")
    
    def is_connected(self) -> bool:
        """Check if connected to PLC"""
        if not self.connected:
            return False
        
        try:
            # Try to read a small amount of data to test connection
            self.client.db_read(1, 0, 1)
            return True
        except:
            self.connected = False
            return False
    
    def read_bit(self, db_number: int, byte_offset: int, bit_offset: int) -> Optional[bool]:
        """
        Read a single bit from PLC
        
        Args:
            db_number: Data block number
            byte_offset: Byte offset
            bit_offset: Bit offset (0-7)
            
        Returns:
            bool: Bit value (True/False) or None if error
        """
        try:
            # Read the byte containing the bit
            data = self.client.db_read(db_number, byte_offset, 1)
            if data:
                # Extract the specific bit
                byte_value = data[0]
                bit_value = bool(byte_value & (1 << bit_offset))
                return bit_value
            return None
        except Exception as e:
            self.logger.error(f"Error reading bit DB{db_number}.DBX{byte_offset}.{bit_offset}: {e}")
            return None
    
    def read_byte(self, db_number: int, byte_offset: int) -> Optional[int]:
        """
        Read a byte from PLC
        
        Args:
            db_number: Data block number
            byte_offset: Byte offset
            
        Returns:
            int: Byte value (0-255) or None if error
        """
        try:
            data = self.client.db_read(db_number, byte_offset, 1)
            if data:
                return data[0]
            return None
        except Exception as e:
            self.logger.error(f"Error reading byte DB{db_number}.DBB{byte_offset}: {e}")
            return None
    
    def read_word(self, db_number: int, byte_offset: int) -> Optional[int]:
        """
        Read a word (16-bit) from PLC
        
        Args:
            db_number: Data block number
            byte_offset: Byte offset (must be even)
            
        Returns:
            int: Word value (0-65535) or None if error
        """
        try:
            data = self.client.db_read(db_number, byte_offset, 2)
            if data and len(data) >= 2:
                # Convert 2 bytes to word (big-endian)
                word_value = (data[0] << 8) | data[1]
                return word_value
            return None
        except Exception as e:
            self.logger.error(f"Error reading word DB{db_number}.DBW{byte_offset}: {e}")
            return None
    
    def read_dword(self, db_number: int, byte_offset: int) -> Optional[int]:
        """
        Read a dword (32-bit) from PLC
        
        Args:
            db_number: Data block number
            byte_offset: Byte offset (must be multiple of 4)
            
        Returns:
            int: DWord value or None if error
        """
        try:
            data = self.client.db_read(db_number, byte_offset, 4)
            if data and len(data) >= 4:
                # Convert 4 bytes to dword (big-endian)
                dword_value = (data[0] << 24) | (data[1] << 16) | (data[2] << 8) | data[3]
                return dword_value
            return None
        except Exception as e:
            self.logger.error(f"Error reading dword DB{db_number}.DBD{byte_offset}: {e}")
            return None
    
    def read_io_by_name(self, io_name: str) -> Optional[Union[bool, int, float]]:
        """
        Read IO value by name using configuration
        
        Args:
            io_name: Name of the IO signal (from IO_MAPPING)
            
        Returns:
            Value of the IO signal (scaled if applicable) or None if error
        """
        if io_name not in IO_MAPPING:
            self.logger.error(f"IO name '{io_name}' not found in configuration")
            return None
        
        io_config = IO_MAPPING[io_name]
        address_info = get_io_address_info(io_config['address'])
        
        try:
            # Read based on data type
            if io_config['type'] == 'bit':
                value = self.read_bit(
                    address_info['db_number'],
                    address_info['byte_offset'],
                    address_info['bit_offset']
                )
            elif io_config['type'] == 'byte':
                value = self.read_byte(
                    address_info['db_number'],
                    address_info['byte_offset']
                )
            elif io_config['type'] == 'word':
                value = self.read_word(
                    address_info['db_number'],
                    address_info['byte_offset']
                )
            elif io_config['type'] == 'dword':
                value = self.read_dword(
                    address_info['db_number'],
                    address_info['byte_offset']
                )
            else:
                self.logger.error(f"Unsupported data type: {io_config['type']}")
                return None
            
            # Apply scale factor if configured
            if value is not None and 'scale_factor' in io_config:
                value = value * io_config['scale_factor']
            
            self.last_read_time = time.time()
            return value
            
        except Exception as e:
            self.logger.error(f"Error reading IO '{io_name}': {e}")
            return None
    
    def read_all_io(self) -> Dict[str, Any]:
        """
        Read all configured IO signals
        
        Returns:
            dict: Dictionary with IO names as keys and values as values
        """
        io_data = {}
        
        for io_name in IO_MAPPING.keys():
            value = self.read_io_by_name(io_name)
            io_data[io_name] = value
        
        return io_data
    
    def read_io_summary(self) -> str:
        """
        Read all IO and format as human-readable summary
        
        Returns:
            str: Formatted IO summary
        """
        io_data = self.read_all_io()
        summary_lines = []
        
        for io_name, value in io_data.items():
            if value is not None:
                io_config = IO_MAPPING[io_name]
                description = io_config['description']
                unit = io_config['unit']
                
                if io_config['type'] == 'bit':
                    status = "ON" if value else "OFF"
                    summary_lines.append(f"- {description}: {status}")
                else:
                    summary_lines.append(f"- {description}: {value} {unit}")
            else:
                summary_lines.append(f"- {IO_MAPPING[io_name]['description']}: ERROR")
        
        return "\n".join(summary_lines)
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test PLC connection and basic functionality
        
        Returns:
            dict: Test results
        """
        results = {
            'connected': False,
            'connection_time': None,
            'test_read': False,
            'error': None
        }
        
        try:
            # Test connection
            if self.connect():
                results['connected'] = True
                results['connection_time'] = time.time()
                
                # Test reading a simple value
                test_value = self.read_byte(1, 0)
                if test_value is not None:
                    results['test_read'] = True
                else:
                    results['error'] = "Could not read test value from PLC"
            else:
                results['error'] = self.last_error
                
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get current connection status
        
        Returns:
            dict: Connection status information
        """
        return {
            'connected': self.is_connected(),
            'ip': self.ip,
            'rack': self.rack,
            'slot': self.slot,
            'connection_time': self.connection_time,
            'last_read_time': self.last_read_time,
            'last_error': self.last_error
        }
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

# Example usage and testing
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Test PLC communicator
    plc = PLCCommunicator()
    
    print("Testing PLC Communication:")
    print(f"Target PLC: {plc.ip}:{plc.rack}/{plc.slot}")
    
    # Test connection
    test_results = plc.test_connection()
    print(f"Connection test: {'✅ PASS' if test_results['connected'] else '❌ FAIL'}")
    
    if test_results['error']:
        print(f"Error: {test_results['error']}")
    else:
        print("✅ Connection successful")
        
        # Test reading all IO
        print("\nReading all configured IO:")
        io_data = plc.read_all_io()
        
        for io_name, value in io_data.items():
            status = f"{value}" if value is not None else "ERROR"
            print(f"  {io_name}: {status}")
        
        # Test IO summary
        print("\nIO Summary:")
        summary = plc.read_io_summary()
        print(summary)
    
    # Cleanup
    plc.disconnect() 