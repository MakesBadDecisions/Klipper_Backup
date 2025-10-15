"""
Core Utilities for Printer Buddy

Common utility functions and helpers.
"""

import logging
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
import re

logger = logging.getLogger(__name__)

def load_config_file(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """
    Load configuration from JSON or YAML file
    
    Args:
        file_path: Path to configuration file
        
    Returns:
        Dict with configuration data or None if error
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        logger.error(f"Config file not found: {file_path}")
        return None
        
    try:
        with open(file_path, 'r') as f:
            if file_path.suffix.lower() in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            elif file_path.suffix.lower() == '.json':
                return json.load(f)
            else:
                # Try to detect format by content
                content = f.read()
                f.seek(0)
                
                if content.strip().startswith('{'):
                    return json.load(f)
                else:
                    return yaml.safe_load(f)
                    
    except Exception as e:
        logger.error(f"Error loading config file {file_path}: {e}")
        return None

def save_config_file(data: Dict[str, Any], file_path: Union[str, Path], format: str = 'yaml') -> bool:
    """
    Save configuration to file
    
    Args:
        data: Configuration data
        file_path: Path to save file
        format: 'yaml' or 'json'
        
    Returns:
        bool: True if successful
    """
    file_path = Path(file_path)
    
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w') as f:
            if format.lower() == 'json':
                json.dump(data, f, indent=2)
            else:
                yaml.dump(data, f, default_flow_style=False, indent=2)
                
        logger.info(f"Config saved to {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving config file {file_path}: {e}")
        return False

def parse_klipper_config(config_path: Union[str, Path]) -> Dict[str, Dict[str, Any]]:
    """
    Parse Klipper printer.cfg file
    
    Args:
        config_path: Path to printer.cfg
        
    Returns:
        Dict with parsed configuration sections
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        logger.error(f"Klipper config not found: {config_path}")
        return {}
        
    config = {}
    current_section = None
    
    try:
        with open(config_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                    
                # Section header
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1].strip()
                    config[current_section] = {}
                    continue
                    
                # Key-value pair
                if current_section and '=' in line:
                    try:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Try to parse as number
                        try:
                            if '.' in value:
                                value = float(value)
                            else:
                                value = int(value)
                        except ValueError:
                            # Keep as string
                            pass
                            
                        config[current_section][key] = value
                        
                    except Exception as e:
                        logger.warning(f"Error parsing line {line_num} in {config_path}: {line} - {e}")
                        
    except Exception as e:
        logger.error(f"Error reading Klipper config {config_path}: {e}")
        
    return config

def validate_move_safe(position: Dict[str, float], limits: Dict[str, Dict[str, float]]) -> bool:
    """
    Validate that a move is within safe limits
    
    Args:
        position: Target position {'x': val, 'y': val, 'z': val}
        limits: Axis limits {'x': {'min': val, 'max': val}, ...}
        
    Returns:
        bool: True if move is safe
    """
    for axis, pos in position.items():
        if axis in limits:
            axis_limits = limits[axis]
            if pos < axis_limits.get('min', float('-inf')) or pos > axis_limits.get('max', float('inf')):
                logger.warning(f"Move unsafe: {axis}={pos} outside limits {axis_limits}")
                return False
                
    return True

def clamp_value(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max"""
    return max(min_val, min(max_val, value))

def setup_logging(log_level: str = 'INFO', log_file: Optional[Path] = None):
    """
    Setup logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
    logger.info(f"Logging configured: level={log_level}, file={log_file}")

def sanitize_gcode(gcode: str) -> str:
    """
    Sanitize G-code for safety
    
    Args:
        gcode: Raw G-code string
        
    Returns:
        str: Sanitized G-code
    """
    lines = []
    
    for line in gcode.split('\n'):
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith(';'):
            continue
            
        # Remove dangerous commands - add more as needed
        dangerous_patterns = [
            r'M112',  # Emergency stop - should only come from safety system
            r'M999',  # Reset after emergency stop
        ]
        
        is_dangerous = False
        for pattern in dangerous_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                logger.warning(f"Removed dangerous G-code: {line}")
                is_dangerous = True
                break
                
        if not is_dangerous:
            lines.append(line)
            
    return '\n'.join(lines)