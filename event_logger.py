import json
import os
from datetime import datetime, date
import glob
from typing import Dict, Any, List
import re

class EventLogger:
    """Event logging system for tracking IO state changes"""
    
    def __init__(self, log_file=None):
        if log_file is None:
            base_dir = os.path.dirname(__file__)
            data_dir = os.path.join(base_dir, 'data')
            os.makedirs(data_dir, exist_ok=True)
            log_file = os.path.join(data_dir, 'io_events.json')
        # Use daily log rotation: io_events_YYYY-MM-DD.json (fallback to single file path if given)
        self.base_dir = os.path.dirname(__file__)
        self.data_dir = os.path.join(self.base_dir, 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        # If a custom file was passed, keep it; otherwise default to daily file
        self.log_file = log_file if log_file else self._today_log_path()
        self.previous_states = {}
        self.max_events = 5000  # Per-file cap to avoid huge daily files
        self.plc_communication_status = None  # Track overall PLC communication
        self.initial_snapshot_logged = False  # Track whether we've logged a system snapshot
        # Debounce removed to capture all fast IO edges

    def _is_fault_tag(self, io_name: str, io_cfg: Dict) -> bool:
        # Only treat explicit fault array items and fault_count as fault-like
        try:
            if io_name == 'fault_count':
                return True
            return bool(re.match(r'^Faults\[\d+\]$', io_name))
        except Exception:
            return False

    def _today_log_path(self) -> str:
        today_str = date.today().isoformat()
        return os.path.join(self.data_dir, f'io_events_{today_str}.json')

    def _list_log_files(self):
        pattern = os.path.join(self.data_dir, 'io_events_*.json')
        files = glob.glob(pattern)
        files.sort(reverse=True)
        return files
        
    def log_event(self, io_name: str, old_value: Any, new_value: Any, io_config: Dict):
        """Log an IO state change event"""
        timestamp = datetime.now().isoformat()
        
        # Determine event type
        event_type = "change"
        if old_value is None:
            event_type = "initialization"
        elif new_value is None:
            event_type = "error"
        elif io_config.get('type') == 'bit':
            if old_value == 0 and new_value == 1:
                event_type = "activated"
            elif old_value == 1 and new_value == 0:
                event_type = "deactivated"
        
        # Special handling for E-Stop events - only for real state changes
        priority = "normal"
        if "stop" in io_name.lower() or "estop" in io_name.lower():
            priority = "critical"
            
            # Only log E-Stop events when we have valid state transitions
            if old_value is not None and new_value is not None:
                if new_value == 0 or new_value == False:
                    event_type = "emergency_stop_pressed"  # Signal lost = E-Stop pressed
                elif new_value == 1 or new_value == True:
                    event_type = "emergency_stop_reset"    # Signal restored = E-Stop reset/healthy
        elif "alarm" in io_name.lower() and new_value == 1:
            priority = "high"
        
        event = {
            'timestamp': timestamp,
            'io_name': io_name,
            'description': io_config.get('description', ''),
            'address': io_config.get('address', ''),
            'old_value': old_value,
            'new_value': new_value,
            'event_type': event_type,
            'priority': priority
        }
        
        # Save event to file
        self._save_event(event)
        
        return event
    
    def log_communication_event(self, is_connected: bool):
        """Log PLC communication status changes"""
        # Skip logging frequent connect/disconnect cycles that are part of normal operation
        # Only log if the state has been stable for a reasonable time or is a real failure
        
        current_time = datetime.now()
        
        # If this is the first time we're tracking communication status
        if self.plc_communication_status is None:
            self.plc_communication_status = is_connected
            return None  # Don't log initial state
        
        # If status hasn't changed, no need to log
        if self.plc_communication_status == is_connected:
            return None
        
        # TODO: In the future, implement persistent connections to avoid these frequent cycles
        # For now, we'll reduce the noise by not logging every connect/disconnect cycle
        # which are part of the normal "connect -> read -> disconnect" pattern
        
        # Only log actual connection failures (when we can't connect at all)
        # vs normal operational connect/disconnect cycles
        if not is_connected:
            # This might be a real connection issue, but let's not spam the log
            # since the app design causes frequent disconnects
            pass
        
        # Update status but don't create log events for routine connect/disconnect
        self.plc_communication_status = is_connected
        return None

    def log_system_snapshot(self, io_data: Dict[str, Dict]):
        """Log a single summary snapshot once per day, not per IO item."""
        try:
            # Avoid duplicate daily snapshots (e.g., dev reload)
            existing = self._load_events()
            if any(e.get('event_type') == 'system_snapshot' for e in (existing or [])):
                self.initial_snapshot_logged = True
                return []

            total = len(io_data or {})
            online = sum(1 for v in (io_data or {}).values() if v.get('status') == 'online')
            errors = sum(1 for v in (io_data or {}).values() if v.get('status') == 'error')
            # Simple faults count: count tags that look like Faults[n] and are ON/True
            faults_active = 0
            try:
                for name, info in (io_data or {}).items():
                    if self._is_fault_tag(name, info):
                        val = info.get('value')
                        if isinstance(val, (int, bool)) and bool(val):
                            faults_active += 1
            except Exception:
                pass

            snapshot_event = {
                'timestamp': datetime.now().isoformat(),
                'io_name': 'SYSTEM',
                'description': 'System startup snapshot',
                'address': '',
                'old_value': None,
                'new_value': None,
                'event_type': 'system_snapshot',
                'priority': 'normal',
                'snapshot_counts': {
                    'total': total,
                    'online': online,
                    'errors': errors,
                    'faults_active': faults_active
                }
            }
            self._save_event(snapshot_event)
            self.initial_snapshot_logged = True
            return [snapshot_event]
        except Exception as e:
            print(f"Error logging system snapshot: {e}")
            return []
    
    def check_and_log_changes(self, current_io_data: Dict, io_mapping: Dict):
        """Check for changes in IO data and log events"""
        events = []
        
        for io_name, current_info in current_io_data.items():
            current_value = current_info.get('value')
            previous_value = self.previous_states.get(io_name)
            
            # If this is the first reading for this tag, set previous and also log an initialization if value is known
            if io_name not in self.previous_states:
                self.previous_states[io_name] = current_value
                if current_value is not None:
                    event = self.log_event(io_name, None, current_value, io_mapping.get(io_name, {}))
                    events.append(event)
                continue
            
            # Check if value has actually changed
            if previous_value != current_value:
                # Log change when current value is known (even if previous was unknown)
                if current_value is not None:
                    io_cfg = io_mapping.get(io_name, {})
                    event = self.log_event(io_name, previous_value, current_value, io_cfg)
                    events.append(event)
                
                # Always update previous state regardless
                self.previous_states[io_name] = current_value
        
        return events
    
    def _save_event(self, event: Dict):
        """Save event to JSON log file"""
        try:
            # Load existing events
            # Always write to today's file
            self.log_file = self._today_log_path()
            events = self._load_events()  # today's events
            
            # Add new event at the beginning
            events.insert(0, event)
            
            # Limit the number of events
            if len(events) > self.max_events:
                events = events[:self.max_events]
            
            # Save back to file
            with open(self.log_file, 'w') as f:
                json.dump(events, f, indent=2)
                
        except Exception as e:
            print(f"Error saving event: {e}")
    
    def _load_events(self) -> List[Dict]:
        """Load events from JSON log file"""
        try:
            # Load today's file; if missing, return empty
            self.log_file = self._today_log_path()
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error loading events: {e}")
            return []
    
    def get_recent_events(self, limit: int = 20) -> List[Dict]:
        """Get the most recent events"""
        events = self._load_events()
        return events[:limit]
    
    def get_events_by_priority(self, priority: str, limit: int = 10) -> List[Dict]:
        """Get events filtered by priority"""
        events = self._load_events()
        filtered = [e for e in events if e.get('priority') == priority]
        return filtered[:limit]
    
    def get_event_statistics(self) -> Dict:
        """Get statistics about logged events"""
        # Today's events from today's file
        today_events = self._load_events()

        # Aggregate totals across all daily files
        total_events = 0
        critical_events = 0
        high_events = 0
        files = self._list_log_files()
        for fp in files:
            try:
                with open(fp, 'r') as f:
                    evs = json.load(f)
                    total_events += len(evs)
                    critical_events += len([e for e in evs if e.get('priority') == 'critical'])
                    high_events += len([e for e in evs if e.get('priority') == 'high'])
            except Exception:
                continue
        
        return {
            'total_events': total_events,
            'critical_events': critical_events,
            'high_priority_events': high_events,
            'events_today': len(today_events),
            'latest_event': today_events[0] if today_events else None
        }
    
    def format_event_for_display(self, event: Dict) -> Dict:
        """Format event for web display"""
        try:
            # Parse timestamp
            timestamp = datetime.fromisoformat(event['timestamp'])
            formatted_time = timestamp.strftime('%H:%M:%S')
            formatted_date = timestamp.strftime('%Y-%m-%d')
            time_ago = self._time_ago(timestamp)
            
            # Format value display
            old_display = self._format_value(event.get('old_value'), event.get('event_type'))
            new_display = self._format_value(event.get('new_value'), event.get('event_type'))
            
            # Create simple change description
            change_desc = f"{old_display} → {new_display}"
            if event.get('event_type') == 'initialization':
                change_desc = f"Started: {new_display}"
            elif event.get('event_type') == 'system_snapshot':
                total = (event.get('snapshot_counts') or {}).get('total', 0)
                change_desc = f"Initial startup IO values recorded ({total} points)"
            elif event.get('event_type') == 'emergency_stop_pressed':
                change_desc = "E-STOP PRESSED"
            elif event.get('event_type') == 'emergency_stop_reset':
                change_desc = "E-STOP RESET / HEALTHY"
            elif event.get('event_type') == 'emergency_stop':
                # Legacy fallback for old events
                if event.get('new_value') == True or event.get('new_value') == 1:
                    change_desc = "E-STOP RESET / HEALTHY"
                else:
                    change_desc = "E-STOP PRESSED"
            elif event.get('event_type') == 'plc_connected':
                change_desc = "PLC CONNECTED"
            elif event.get('event_type') == 'plc_disconnected':
                change_desc = "PLC DISCONNECTED"
            elif event.get('event_type') == 'activated':
                change_desc = "ON"
            elif event.get('event_type') == 'deactivated':
                change_desc = "OFF"
            elif event.get('event_type') == 'error':
                change_desc = "ERROR"
            
            # Clean up the description - remove redundant info
            description = event.get('description', '')
            if '(0=OFF, 1=ON)' in description:
                description = description.replace(' (0=OFF, 1=ON)', '')
            
            return {
                'timestamp': event['timestamp'],
                'formatted_time': formatted_time,
                'formatted_date': formatted_date,
                'time_ago': time_ago,
                'io_name': event.get('io_name', ''),
                'description': description,
                'change_description': change_desc,
                'event_type': event.get('event_type', 'change'),
                'priority': event.get('priority', 'normal'),
                'address': event.get('address', '')
            }
        except Exception as e:
            print(f"Error formatting event: {e}")
            return event
    
    def _format_value(self, value, event_type=None):
        """Format a value for display"""
        if value is None:
            return "NULL"
        elif isinstance(value, bool) or (isinstance(value, int) and value in [0, 1]):
            return "ON" if value else "OFF"
        else:
            return str(value)
    
    def _time_ago(self, timestamp):
        """Calculate time ago string"""
        try:
            now = datetime.now()
            diff = now - timestamp
            
            if diff.days > 0:
                return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            else:
                return "Just now"
        except:
            return "Unknown"

# Global event logger instance
event_logger = EventLogger()
