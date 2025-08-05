import json
import os
from datetime import datetime
from typing import Dict, Any, List

class EventLogger:
    """Event logging system for tracking IO state changes"""
    
    def __init__(self, log_file='io_events.json'):
        self.log_file = log_file
        self.previous_states = {}
        self.max_events = 1000  # Maximum number of events to keep
        
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
        
        # Special handling for E-Stop events
        priority = "normal"
        if "stop" in io_name.lower() or "estop" in io_name.lower():
            priority = "critical"
            if new_value == 1 or new_value == True:
                event_type = "emergency_stop"  # E-Stop activated
            elif new_value == 0 or new_value == False:
                event_type = "emergency_stop"  # E-Stop deactivated (still important!)
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
    
    def check_and_log_changes(self, current_io_data: Dict, io_mapping: Dict):
        """Check for changes in IO data and log events"""
        events = []
        
        for io_name, current_info in current_io_data.items():
            current_value = current_info.get('value')
            previous_value = self.previous_states.get(io_name)
            
            # Skip if this is the first reading (initialization) - just store the state
            if io_name not in self.previous_states:
                self.previous_states[io_name] = current_value
                continue
            
            # Check if value has actually changed
            if previous_value != current_value:
                event = self.log_event(
                    io_name, 
                    previous_value, 
                    current_value, 
                    io_mapping.get(io_name, {})
                )
                events.append(event)
                
                # Update previous state
                self.previous_states[io_name] = current_value
        
        return events
    
    def _save_event(self, event: Dict):
        """Save event to JSON log file"""
        try:
            # Load existing events
            events = self._load_events()
            
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
        events = self._load_events()
        
        total_events = len(events)
        critical_events = len([e for e in events if e.get('priority') == 'critical'])
        high_events = len([e for e in events if e.get('priority') == 'high'])
        
        # Get events from today
        today = datetime.now().date()
        today_events = []
        for event in events:
            try:
                event_date = datetime.fromisoformat(event['timestamp']).date()
                if event_date == today:
                    today_events.append(event)
            except:
                continue
        
        return {
            'total_events': total_events,
            'critical_events': critical_events,
            'high_priority_events': high_events,
            'events_today': len(today_events),
            'latest_event': events[0] if events else None
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
            elif event.get('event_type') == 'emergency_stop':
                # Be explicit about E-Stop state
                if event.get('new_value') == True or event.get('new_value') == 1:
                    change_desc = "E-STOP ACTIVATED"
                else:
                    change_desc = "E-STOP RELEASED"
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
