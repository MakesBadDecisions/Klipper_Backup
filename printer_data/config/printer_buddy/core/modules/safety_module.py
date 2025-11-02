"""
Safety Module for Printer Buddy

Handles emergency stop and safety systems.
"""

import logging
from typing import Dict, Any

from . import SafetyModule, ModuleStatus, ModuleCapability

logger = logging.getLogger(__name__)

class PrinterSafetyModule(SafetyModule):
    """
    Printer safety management module
    
    Responsibilities:
    - Emergency stop functionality
    - Safety limit validation
    - Movement safety checks
    - Temperature safety monitoring
    """
    
    def __init__(self):
        super().__init__('safety', 'Safety Manager', '1.0.0')
        
        self.emergency_stop_active = False
        self.safety_limits = {}
        
    async def initialize(self) -> bool:
        """Initialize the safety module"""
        try:
            self.update_status(ModuleStatus.INITIALIZING)
            logger.info("Initializing Safety Module...")
            
            # Subscribe to emergency events
            if self.event_bus:
                self.event_bus.subscribe('emergency_stop', self._handle_emergency_stop)
                self.event_bus.subscribe('config_loaded', self._update_safety_limits)
                
            # Initialize safety state
            if self.state_manager:
                self.state_manager.set('system.safety_enabled', True)
                self.emergency_stop_active = self.state_manager.get('system.emergency_stop', False)
                
            self.update_status(ModuleStatus.READY)
            logger.info("Safety Module initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Safety Module: {e}")
            self.update_status(ModuleStatus.ERROR)
            return False
            
    async def shutdown(self):
        """Shutdown the safety module"""
        # Ensure system is in safe state before shutdown
        self.enter_safe_mode()
        self.update_status(ModuleStatus.DISABLED)
        logger.info("Safety Module shutdown")
        
    def get_status(self) -> Dict[str, Any]:
        """Get current module status"""
        return {
            'module_id': self.module_id,
            'name': self.name,
            'status': self.status.value,
            'emergency_stop_active': self.emergency_stop_active,
            'safety_limits_loaded': bool(self.safety_limits)
        }
        
    def validate_safe_state(self) -> bool:
        """Validate that the system is in a safe state"""
        if self.emergency_stop_active:
            return False
            
        if not self.state_manager:
            return False
            
        # Check system status
        system_status = self.state_manager.get('system.status')
        if system_status in ['error', 'emergency_stop']:
            return False
            
        return True
        
    def enter_safe_mode(self):
        """Enter safe mode - stop all potentially dangerous operations"""
        logger.critical("ENTERING SAFE MODE")
        
        # Set emergency stop state
        self.emergency_stop_active = True
        
        if self.state_manager:
            self.state_manager.emergency_stop()
            
        # Publish emergency event
        if self.event_bus:
            self.event_bus.publish(
                'emergency_stop',
                self.module_id,
                {'reason': 'Safe mode entered', 'timestamp': time.time()},
                priority=10  # Highest priority
            )
            
    def emergency_stop(self):
        """Handle emergency stop activation"""
        logger.critical("EMERGENCY STOP ACTIVATED")
        self.enter_safe_mode()
        
    def clear_emergency_stop(self):
        """Clear emergency stop state (if safe to do so)"""
        if not self.validate_system_safety():
            logger.warning("Cannot clear emergency stop - system not safe")
            return False
            
        self.emergency_stop_active = False
        
        if self.state_manager:
            self.state_manager.clear_emergency_stop()
            
        if self.event_bus:
            self.event_bus.publish(
                'emergency_stop_cleared',
                self.module_id,
                {'timestamp': time.time()}
            )
            
        logger.info("Emergency stop cleared")
        return True
        
    def validate_movement(self, position: Dict[str, float]) -> bool:
        """Validate that a movement is within safe limits"""
        if not self.validate_safe_state():
            return False
            
        # Check against configured limits
        for axis, pos in position.items():
            if axis in self.safety_limits:
                limits = self.safety_limits[axis]
                if pos < limits.get('min', float('-inf')) or pos > limits.get('max', float('inf')):
                    logger.warning(f"Movement rejected: {axis}={pos} outside limits {limits}")
                    return False
                    
        return True
        
    def validate_temperature(self, sensor: str, temperature: float) -> bool:
        """Validate that a temperature is within safe limits"""
        if not self.validate_safe_state():
            return False
            
        # Basic temperature safety checks
        max_temps = {
            'bed': 120,  # °C
            'extruder': 300,  # °C
            'chamber': 60   # °C
        }
        
        max_temp = max_temps.get(sensor, 250)
        
        if temperature > max_temp:
            logger.error(f"Temperature {temperature}°C exceeds safe limit {max_temp}°C for {sensor}")
            return False
            
        return True
        
    def validate_system_safety(self) -> bool:
        """Comprehensive system safety validation"""
        checks = []
        
        # Check module status
        checks.append(('Module healthy', self.is_healthy()))
        
        # Check emergency stop state
        checks.append(('No emergency stop', not self.emergency_stop_active))
        
        # Check system status
        if self.state_manager:
            system_status = self.state_manager.get('system.status')
            checks.append(('System status OK', system_status not in ['error', 'emergency_stop']))
            
        # Log validation results
        failed_checks = [name for name, passed in checks if not passed]
        if failed_checks:
            logger.warning(f"Safety validation failed: {', '.join(failed_checks)}")
            return False
            
        return True
        
    def _handle_emergency_stop(self, event):
        """Handle emergency stop event"""
        logger.critical(f"Emergency stop event received from {event.source}")
        self.enter_safe_mode()
        
    def _update_safety_limits(self, event):
        """Update safety limits from configuration"""
        if self.core_manager and hasattr(self.core_manager, 'modules'):
            config_module = self.core_manager.modules.get('config')
            if config_module:
                self.safety_limits = config_module.get_printer_limits()
                logger.info(f"Safety limits updated: {self.safety_limits}")
                
import time