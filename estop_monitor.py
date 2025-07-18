"""
E-Stop Monitoring Module for E-Stop AI Status Reporter
Handles continuous E-Stop monitoring, edge detection, and automatic report generation
"""

import time
import threading
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from plc_communicator import PLCCommunicator
from config import ESTOP_CONFIG, IO_MAPPING, PROMPT_TEMPLATES

class EStopMonitor:
    """
    E-Stop monitoring class
    Continuously monitors E-Stop status and generates reports on activation
    """
    
    def __init__(self, plc_communicator: PLCCommunicator = None):
        """
        Initialize E-Stop monitor
        
        Args:
            plc_communicator: PLC communicator instance (creates new one if None)
        """
        self.plc = plc_communicator or PLCCommunicator()
        self.logger = logging.getLogger(__name__)
        
        # Monitoring state
        self.monitoring = False
        self.monitor_thread = None
        self.last_estop_state = False
        self.estop_triggered = False
        self.last_trigger_time = None
        
        # Configuration
        self.polling_interval = ESTOP_CONFIG['polling_interval']
        self.debounce_time = ESTOP_CONFIG['debounce_time']
        self.edge_detection = ESTOP_CONFIG['edge_detection']
        self.auto_reset = ESTOP_CONFIG['auto_reset']
        self.reset_delay = ESTOP_CONFIG['reset_delay']
        
        # Callbacks
        self.on_estop_triggered: Optional[Callable] = None
        self.on_status_changed: Optional[Callable] = None
        
        # Event history
        self.event_history = []
        self.max_history = 100
        
    def start_monitoring(self) -> bool:
        """
        Start E-Stop monitoring in background thread
        
        Returns:
            bool: True if monitoring started successfully
        """
        if self.monitoring:
            self.logger.warning("E-Stop monitoring already running")
            return True
        
        try:
            # Connect to PLC if not already connected
            if not self.plc.is_connected():
                if not self.plc.connect():
                    self.logger.error("Failed to connect to PLC for monitoring")
                    return False
            
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            
            self.logger.info("E-Stop monitoring started")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting E-Stop monitoring: {e}")
            self.monitoring = False
            return False
    
    def stop_monitoring(self):
        """Stop E-Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)
        
        self.logger.info("E-Stop monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        self.logger.info("E-Stop monitoring loop started")
        
        while self.monitoring:
            try:
                # Read current E-Stop state
                current_estop_state = self.plc.read_io_by_name('emergency_stop')
                
                if current_estop_state is None:
                    self.logger.warning("Could not read E-Stop state")
                    time.sleep(self.polling_interval)
                    continue
                
                # Check for edge detection (OFF → ON transition)
                if self.edge_detection and current_estop_state and not self.last_estop_state:
                    self._handle_estop_triggered()
                
                # Update state
                if self.last_estop_state != current_estop_state:
                    self._handle_status_change(current_estop_state)
                
                self.last_estop_state = current_estop_state
                
                # Sleep for polling interval
                time.sleep(self.polling_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.polling_interval)
        
        self.logger.info("E-Stop monitoring loop ended")
    
    def _handle_estop_triggered(self):
        """Handle E-Stop trigger event"""
        self.logger.warning("EMERGENCY STOP TRIGGERED!")
        
        # Add debounce delay
        time.sleep(self.debounce_time)
        
        # Verify E-Stop is still active after debounce
        if not self.plc.read_io_by_name('emergency_stop'):
            self.logger.info("E-Stop debounced - false trigger")
            return
        
        # Record trigger
        self.estop_triggered = True
        self.last_trigger_time = datetime.now()
        
        # Create event record
        event = {
            'timestamp': self.last_trigger_time,
            'type': 'emergency_stop_triggered',
            'description': 'Emergency stop button pressed',
            'io_summary': self.plc.read_io_summary()
        }
        
        self._add_event_to_history(event)
        
        # Call callback if registered
        if self.on_estop_triggered:
            try:
                self.on_estop_triggered(event)
            except Exception as e:
                self.logger.error(f"Error in E-Stop callback: {e}")
        
        self.logger.info("E-Stop trigger handled")
    
    def _handle_status_change(self, new_state: bool):
        """Handle E-Stop status change"""
        status = "ACTIVATED" if new_state else "DEACTIVATED"
        self.logger.info(f"E-Stop status changed: {status}")
        
        # Create event record
        event = {
            'timestamp': datetime.now(),
            'type': 'estop_status_change',
            'description': f'E-Stop {status.lower()}',
            'state': new_state
        }
        
        self._add_event_to_history(event)
        
        # Call callback if registered
        if self.on_status_changed:
            try:
                self.on_status_changed(event)
            except Exception as e:
                self.logger.error(f"Error in status change callback: {e}")
    
    def _add_event_to_history(self, event: Dict[str, Any]):
        """Add event to history (with size limit)"""
        self.event_history.append(event)
        
        # Keep only recent events
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
    
    def get_current_status(self) -> Dict[str, Any]:
        """
        Get current E-Stop monitoring status
        
        Returns:
            dict: Current status information
        """
        return {
            'monitoring': self.monitoring,
            'connected': self.plc.is_connected(),
            'last_estop_state': self.last_estop_state,
            'estop_triggered': self.estop_triggered,
            'last_trigger_time': self.last_trigger_time,
            'event_count': len(self.event_history),
            'polling_interval': self.polling_interval
        }
    
    def get_event_history(self, limit: int = None) -> list:
        """
        Get event history
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            list: Event history
        """
        if limit is None:
            return self.event_history.copy()
        else:
            return self.event_history[-limit:]
    
    def reset_estop_state(self):
        """Reset E-Stop triggered state (for testing)"""
        self.estop_triggered = False
        self.last_trigger_time = None
        self.logger.info("E-Stop state reset")
    
    def test_estop_detection(self) -> Dict[str, Any]:
        """
        Test E-Stop detection functionality
        
        Returns:
            dict: Test results
        """
        results = {
            'plc_connected': False,
            'estop_readable': False,
            'current_state': None,
            'error': None
        }
        
        try:
            # Test PLC connection
            if self.plc.is_connected():
                results['plc_connected'] = True
                
                # Test reading E-Stop state
                estop_state = self.plc.read_io_by_name('emergency_stop')
                if estop_state is not None:
                    results['estop_readable'] = True
                    results['current_state'] = estop_state
                else:
                    results['error'] = "Could not read E-Stop state"
            else:
                results['error'] = "PLC not connected"
                
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def get_estop_summary(self) -> str:
        """
        Get E-Stop status summary
        
        Returns:
            str: Human-readable E-Stop summary
        """
        status = self.get_current_status()
        
        summary_lines = [
            f"E-Stop Monitoring Status:",
            f"- Monitoring: {'ACTIVE' if status['monitoring'] else 'INACTIVE'}",
            f"- PLC Connected: {'YES' if status['connected'] else 'NO'}",
            f"- Current State: {'ACTIVATED' if status['last_estop_state'] else 'DEACTIVATED'}",
            f"- Triggered: {'YES' if status['estop_triggered'] else 'NO'}",
        ]
        
        if status['last_trigger_time']:
            summary_lines.append(f"- Last Trigger: {status['last_trigger_time']}")
        
        summary_lines.append(f"- Events Recorded: {status['event_count']}")
        
        return "\n".join(summary_lines)

# Example usage and testing
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Test E-Stop monitor
    print("Testing E-Stop Monitor:")
    
    plc = PLCCommunicator()
    monitor = EStopMonitor(plc)
    
    # Test connection and detection
    test_results = monitor.test_estop_detection()
    print(f"E-Stop Detection Test: {'✅ PASS' if test_results['estop_readable'] else '❌ FAIL'}")
    
    if test_results['error']:
        print(f"Error: {test_results['error']}")
    else:
        print(f"Current E-Stop State: {'ACTIVATED' if test_results['current_state'] else 'DEACTIVATED'}")
        
        # Show summary
        print("\nE-Stop Summary:")
        summary = monitor.get_estop_summary()
        print(summary)
    
    # Cleanup
    monitor.stop_monitoring()
    plc.disconnect() 