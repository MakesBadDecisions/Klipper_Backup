"""
Base Module System for Printer Buddy Core

Provides the foundation for all hardware and functionality modules.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)

class ModuleStatus(Enum):
    """Module status enumeration"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"

class ModuleCapability(Enum):
    """Module capability flags"""
    SAFETY_CRITICAL = "safety_critical"
    COMMISSIONING = "commissioning"
    CALIBRATION = "calibration"
    MONITORING = "monitoring"
    HARDWARE_CONTROL = "hardware_control"

class BaseModule(ABC):
    """
    Base class for all Printer Buddy modules
    
    Modules handle specific hardware or functionality areas:
    - Safety systems
    - Commissioning tests
    - Hardware calibration
    - Monitoring systems
    """
    
    def __init__(self, module_id: str, name: str, version: str = "1.0.0"):
        self.module_id = module_id
        self.name = name
        self.version = version
        self.status = ModuleStatus.UNINITIALIZED
        self.capabilities: List[ModuleCapability] = []
        self.config: Dict[str, Any] = {}
        self.dependencies: List[str] = []
        
        # Will be injected by core manager
        self.core_manager = None
        self.event_bus = None
        self.state_manager = None
        
        logger.info(f"Module created: {self.name} ({self.module_id})")
        
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the module
        
        Returns:
            bool: True if initialization successful
        """
        pass
        
    @abstractmethod
    async def shutdown(self):
        """Shutdown the module cleanly"""
        pass
        
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get current module status
        
        Returns:
            Dict containing status information
        """
        pass
        
    def set_dependencies(self, core_manager, event_bus, state_manager):
        """Inject core dependencies"""
        self.core_manager = core_manager
        self.event_bus = event_bus
        self.state_manager = state_manager
        
    def add_capability(self, capability: ModuleCapability):
        """Add a capability to this module"""
        if capability not in self.capabilities:
            self.capabilities.append(capability)
            
    def has_capability(self, capability: ModuleCapability) -> bool:
        """Check if module has a specific capability"""
        return capability in self.capabilities
        
    def update_status(self, status: ModuleStatus, message: Optional[str] = None):
        """Update module status and notify system"""
        old_status = self.status
        self.status = status
        
        if self.event_bus:
            self.event_bus.publish(
                'module_status_changed',
                self.module_id,
                {
                    'module_id': self.module_id,
                    'old_status': old_status.value,
                    'new_status': status.value,
                    'message': message
                }
            )
            
        logger.info(f"Module {self.module_id} status: {old_status.value} -> {status.value}")
        
    def update_config(self, config: Dict[str, Any]):
        """Update module configuration"""
        self.config.update(config)
        
        if self.event_bus:
            self.event_bus.publish(
                'module_config_updated',
                self.module_id,
                {
                    'module_id': self.module_id,
                    'config': self.config
                }
            )
            
    def emergency_stop(self):
        """Handle emergency stop - override in safety-critical modules"""
        logger.warning(f"Emergency stop called on module {self.module_id}")
        
    def is_healthy(self) -> bool:
        """Check if module is in healthy state"""
        return self.status in [ModuleStatus.READY, ModuleStatus.ACTIVE]

class SafetyModule(BaseModule):
    """
    Base class for safety-critical modules
    
    Safety modules have special requirements:
    - Must respond to emergency stops
    - Higher priority event handling
    - Additional validation
    """
    
    def __init__(self, module_id: str, name: str, version: str = "1.0.0"):
        super().__init__(module_id, name, version)
        self.add_capability(ModuleCapability.SAFETY_CRITICAL)
        
    @abstractmethod
    def validate_safe_state(self) -> bool:
        """
        Validate that the module is in a safe state
        
        Returns:
            bool: True if safe to continue operations
        """
        pass
        
    @abstractmethod
    def enter_safe_mode(self):
        """Enter safe mode - stop all potentially dangerous operations"""
        pass

class CommissioningModule(BaseModule):
    """
    Base class for commissioning test modules
    
    Commissioning modules run tests and validations:
    - Movement tests
    - Heating tests
    - Sensor validation
    - Safety verification
    """
    
    def __init__(self, module_id: str, name: str, version: str = "1.0.0"):
        super().__init__(module_id, name, version)
        self.add_capability(ModuleCapability.COMMISSIONING)
        
    @abstractmethod
    async def run_test(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a commissioning test
        
        Args:
            test_config: Test configuration parameters
            
        Returns:
            Dict containing test results
        """
        pass
        
    @abstractmethod
    def get_test_info(self) -> Dict[str, Any]:
        """
        Get information about available tests
        
        Returns:
            Dict describing test capabilities
        """
        pass