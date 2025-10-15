"""
Status Module for Printer Buddy

Handles system status monitoring and reporting.
"""

import logging
from typing import Dict, Any
import time

from . import BaseModule, ModuleStatus, ModuleCapability

logger = logging.getLogger(__name__)

class StatusModule(BaseModule):
    """
    System status monitoring module
    
    Responsibilities:
    - Monitor system health
    - Track uptime
    - Report module statuses
    - Handle status requests
    """
    
    def __init__(self):
        super().__init__('status', 'Status Monitor', '1.0.0')
        self.add_capability(ModuleCapability.MONITORING)
        
        self.start_time = None
        
    async def initialize(self) -> bool:
        """Initialize the status module"""
        try:
            self.update_status(ModuleStatus.INITIALIZING)
            logger.info("Initializing Status Module...")
            
            self.start_time = time.time()
            
            # Update system startup info
            if self.state_manager:
                self.state_manager.set('system.startup_time', time.time())
                self.state_manager.set('system.status', 'ready')
                
            self.update_status(ModuleStatus.READY)
            logger.info("Status Module initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Status Module: {e}")
            self.update_status(ModuleStatus.ERROR)
            return False
            
    async def shutdown(self):
        """Shutdown the status module"""
        self.update_status(ModuleStatus.DISABLED)
        logger.info("Status Module shutdown")
        
    def get_status(self) -> Dict[str, Any]:
        """Get current module status"""
        uptime = time.time() - self.start_time if self.start_time else 0
        
        return {
            'module_id': self.module_id,
            'name': self.name,
            'status': self.status.value,
            'uptime_seconds': uptime,
            'start_time': self.start_time
        }
        
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        system_status = {
            'timestamp': time.time(),
            'uptime': time.time() - self.start_time if self.start_time else 0,
            'system_status': 'ready',
            'emergency_stop': False,
            'modules': {}
        }
        
        # Get status from state manager if available
        if self.state_manager:
            system_status.update({
                'system_status': self.state_manager.get('system.status', 'unknown'),
                'emergency_stop': self.state_manager.get('system.emergency_stop', False),
                'safety_enabled': self.state_manager.get('system.safety_enabled', True)
            })
            
        # Get module statuses from core manager
        if self.core_manager and hasattr(self.core_manager, 'modules'):
            for module_id, module in self.core_manager.modules.items():
                system_status['modules'][module_id] = {
                    'name': module.name,
                    'status': module.status.value,
                    'healthy': module.is_healthy()
                }
                
        return system_status