"""
State Manager for Printer Buddy Core

Centralized state management with thread safety and persistence.
"""

import threading
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import copy

logger = logging.getLogger(__name__)

class StateManager:
    """
    Thread-safe state management for Printer Buddy
    
    Manages:
    - Printer configuration state
    - Current operation state
    - Safety parameters
    - Module states
    - Persistent storage
    """
    
    def __init__(self, state_file: Optional[Path] = None):
        self._state: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._state_file = state_file
        self._callbacks: Dict[str, List[callable]] = {}
        
        # Initialize default state structure
        self._initialize_default_state()
        
        # Load from file if exists
        if self._state_file and self._state_file.exists():
            self.load_state()
            
    def _initialize_default_state(self):
        """Initialize default state structure"""
        with self._lock:
            self._state = {
                'system': {
                    'status': 'initializing',
                    'startup_time': datetime.now().isoformat(),
                    'version': '2.0.0',
                    'emergency_stop': False,
                    'safety_enabled': True
                },
                'printer': {
                    'config_loaded': False,
                    'config_file': None,
                    'homed': {'x': False, 'y': False, 'z': False},
                    'position': {'x': 0.0, 'y': 0.0, 'z': 0.0},
                    'temperatures': {},
                    'limits': {}
                },
                'modules': {},
                'commissioning': {
                    'active': False,
                    'current_test': None,
                    'results': [],
                    'progress': 0
                }
            }
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get state value by key path (e.g., 'printer.position.x')"""
        with self._lock:
            keys = key.split('.')
            current = self._state
            
            try:
                for k in keys:
                    current = current[k]
                return copy.deepcopy(current)
            except (KeyError, TypeError):
                return default
                
    def set(self, key: str, value: Any, notify: bool = True):
        """Set state value by key path"""
        with self._lock:
            keys = key.split('.')
            current = self._state
            
            # Navigate to parent of target key
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
                
            # Set the value
            old_value = current.get(keys[-1])
            current[keys[-1]] = value
            
            logger.debug(f"State updated: {key} = {value}")
            
            # Notify callbacks if value changed
            if notify and old_value != value:
                self._notify_callbacks(key, value, old_value)
                
    def update(self, updates: Dict[str, Any], notify: bool = True):
        """Batch update multiple state values"""
        with self._lock:
            for key, value in updates.items():
                self.set(key, value, notify=False)
                
            if notify:
                for key, value in updates.items():
                    self._notify_callbacks(key, value, self.get(key))
                    
    def delete(self, key: str):
        """Delete a state key"""
        with self._lock:
            keys = key.split('.')
            current = self._state
            
            try:
                for k in keys[:-1]:
                    current = current[k]
                del current[keys[-1]]
                logger.debug(f"State deleted: {key}")
            except KeyError:
                logger.warning(f"Attempted to delete non-existent key: {key}")
                
    def get_all(self) -> Dict[str, Any]:
        """Get complete state (deep copy)"""
        with self._lock:
            return copy.deepcopy(self._state)
            
    def register_callback(self, key_pattern: str, callback: callable):
        """Register callback for state changes"""
        if key_pattern not in self._callbacks:
            self._callbacks[key_pattern] = []
        self._callbacks[key_pattern].append(callback)
        logger.debug(f"Registered callback for: {key_pattern}")
        
    def _notify_callbacks(self, key: str, new_value: Any, old_value: Any):
        """Notify registered callbacks of state changes"""
        for pattern, callbacks in self._callbacks.items():
            if self._key_matches_pattern(key, pattern):
                for callback in callbacks:
                    try:
                        callback(key, new_value, old_value)
                    except Exception as e:
                        logger.error(f"Error in state callback: {e}")
                        
    def _key_matches_pattern(self, key: str, pattern: str) -> bool:
        """Check if key matches callback pattern"""
        # Simple wildcard matching - can be enhanced later
        if pattern == '*':
            return True
        if pattern.endswith('*'):
            return key.startswith(pattern[:-1])
        return key == pattern
        
    def save_state(self):
        """Save state to file"""
        if not self._state_file:
            return
            
        try:
            with self._lock:
                state_copy = copy.deepcopy(self._state)
                
            with open(self._state_file, 'w') as f:
                json.dump(state_copy, f, indent=2, default=str)
                
            logger.info(f"State saved to {self._state_file}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            
    def load_state(self):
        """Load state from file"""
        if not self._state_file or not self._state_file.exists():
            return
            
        try:
            with open(self._state_file, 'r') as f:
                loaded_state = json.load(f)
                
            with self._lock:
                # Merge loaded state with defaults
                self._merge_state(self._state, loaded_state)
                
            logger.info(f"State loaded from {self._state_file}")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            
    def _merge_state(self, default_state: Dict, loaded_state: Dict):
        """Merge loaded state with default state structure"""
        for key, value in loaded_state.items():
            if key in default_state and isinstance(default_state[key], dict) and isinstance(value, dict):
                self._merge_state(default_state[key], value)
            else:
                default_state[key] = value
                
    def emergency_stop(self):
        """Set emergency stop state"""
        with self._lock:
            self.set('system.emergency_stop', True)
            self.set('system.status', 'emergency_stop')
            logger.critical("EMERGENCY STOP ACTIVATED")
            
    def clear_emergency_stop(self):
        """Clear emergency stop state"""
        with self._lock:
            self.set('system.emergency_stop', False)
            self.set('system.status', 'ready')
            logger.info("Emergency stop cleared")
            
    def is_safe_to_operate(self) -> bool:
        """Check if system is in safe operating state"""
        with self._lock:
            return (
                not self.get('system.emergency_stop', True) and
                self.get('system.safety_enabled', True) and
                self.get('system.status') not in ['error', 'emergency_stop']
            )