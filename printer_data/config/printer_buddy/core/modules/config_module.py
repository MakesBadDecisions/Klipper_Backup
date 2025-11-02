"""
Configuration Module for Printer Buddy

Handles printer.cfg parsing and configuration management.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from . import BaseModule, ModuleStatus, ModuleCapability

logger = logging.getLogger(__name__)

class ConfigModule(BaseModule):
    """
    Configuration management module
    
    Responsibilities:
    - Parse printer.cfg file
    - Extract safety limits
    - Monitor configuration changes
    - Validate configuration
    """
    
    def __init__(self):
        super().__init__('config', 'Configuration Manager', '1.0.0')
        self.add_capability(ModuleCapability.SAFETY_CRITICAL)
        
        self.printer_config = {}
        self.config_file_path = None
        
    async def initialize(self) -> bool:
        """Initialize the configuration module"""
        try:
            self.update_status(ModuleStatus.INITIALIZING)
            logger.info("Initializing Configuration Module...")
            
            # Find printer.cfg file
            self.config_file_path = self._find_printer_config()
            
            if self.config_file_path:
                # Load and parse configuration
                await self._load_printer_config()
                
                self.update_status(ModuleStatus.READY)
                logger.info("Configuration Module initialized successfully")
                return True
            else:
                logger.error("printer.cfg file not found")
                self.update_status(ModuleStatus.ERROR)
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize Configuration Module: {e}")
            self.update_status(ModuleStatus.ERROR)
            return False
            
    async def shutdown(self):
        """Shutdown the configuration module"""
        self.update_status(ModuleStatus.DISABLED)
        logger.info("Configuration Module shutdown")
        
    def get_status(self) -> Dict[str, Any]:
        """Get current module status"""
        return {
            'module_id': self.module_id,
            'name': self.name,
            'status': self.status.value,
            'config_file': str(self.config_file_path) if self.config_file_path else None,
            'config_loaded': bool(self.printer_config),
            'sections_count': len(self.printer_config)
        }
        
    def _find_printer_config(self) -> Optional[Path]:
        """Find printer.cfg file in common locations"""
        search_paths = [
            Path.cwd() / 'printer.cfg',
            Path('/home/pi/printer_data/config/printer.cfg'),
            Path('/home/pi/klipper_config/printer.cfg'),
            Path('../printer.cfg'),
            Path('../../printer.cfg')
        ]
        
        for path in search_paths:
            if path.exists():
                logger.info(f"Found printer.cfg at: {path}")
                return path
                
        return None
        
    async def _load_printer_config(self):
        """Load and parse printer configuration"""
        if not self.config_file_path:
            return
            
        try:
            # Use the utils parser
            if self.core_manager and hasattr(self.core_manager, 'utils'):
                self.printer_config = self.core_manager.utils.parse_klipper_config(self.config_file_path)
            else:
                # Fallback basic parsing
                self.printer_config = self._basic_config_parse()
                
            # Update state manager with configuration
            if self.state_manager:
                self.state_manager.set('printer.config_loaded', True)
                self.state_manager.set('printer.config_file', str(self.config_file_path))
                self.state_manager.set('printer.limits', self._extract_limits())
                
            # Publish configuration loaded event
            if self.event_bus:
                self.event_bus.publish(
                    'config_loaded',
                    self.module_id,
                    {
                        'file_path': str(self.config_file_path),
                        'sections': list(self.printer_config.keys())
                    }
                )
                
            logger.info(f"Loaded configuration with {len(self.printer_config)} sections")
            
        except Exception as e:
            logger.error(f"Failed to load printer configuration: {e}")
            raise
            
    def _basic_config_parse(self) -> Dict[str, Dict[str, Any]]:
        """Basic configuration parsing fallback"""
        config = {}
        current_section = None
        
        try:
            with open(self.config_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    
                    if not line or line.startswith('#'):
                        continue
                        
                    if line.startswith('[') and line.endswith(']'):
                        current_section = line[1:-1]
                        config[current_section] = {}
                    elif current_section and '=' in line:
                        key, value = line.split('=', 1)
                        config[current_section][key.strip()] = value.strip()
                        
        except Exception as e:
            logger.error(f"Basic config parsing failed: {e}")
            
        return config
        
    def _extract_limits(self) -> Dict[str, Dict[str, float]]:
        """Extract movement limits from configuration"""
        limits = {}
        
        # Extract stepper limits
        for section_name, section_data in self.printer_config.items():
            if section_name.startswith('stepper_'):
                axis = section_name.replace('stepper_', '')
                if axis in ['x', 'y', 'z']:
                    limits[axis] = {}
                    
                    if 'position_min' in section_data:
                        try:
                            limits[axis]['min'] = float(section_data['position_min'])
                        except ValueError:
                            pass
                            
                    if 'position_max' in section_data:
                        try:
                            limits[axis]['max'] = float(section_data['position_max'])
                        except ValueError:
                            pass
                            
        return limits
        
    def get_printer_limits(self) -> Dict[str, Dict[str, float]]:
        """Get movement limits for safety validation"""
        return self._extract_limits()
        
    def get_section(self, section_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific configuration section"""
        return self.printer_config.get(section_name)
        
    def has_section(self, section_name: str) -> bool:
        """Check if configuration section exists"""
        return section_name in self.printer_config
        
    def get_all_sections(self) -> Dict[str, Dict[str, Any]]:
        """Get all configuration sections"""
        return self.printer_config.copy()