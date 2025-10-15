#!/usr/bin/env python3
"""
Printer Buddy v2.0 - Python Core Manager

Three-Layer Architecture:
- Python Core Layer (this file) - Business logic, state management, modules
- API Layer - HTTP server exposing core functionality  
- UI Layers - Web (JavaScript) + KlipperScreen (Python)

This is the central manager that coordinates all modules and maintains system state.
"""

import asyncio
import time
import logging
import configparser
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from .event_bus import EventBus
from .state_manager import StateManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Abstract interfaces for hardware abstraction
class PrinterManagerInterface(ABC):
    """Abstract interface for printer hardware communication"""
    
    @abstractmethod
    async def get_printer_status(self) -> Dict[str, Any]:
        """Get current printer status from hardware"""
        pass
    
    @abstractmethod
    async def send_gcode(self, gcode: str) -> str:
        """Send gcode command to printer hardware"""
        pass
    
    @abstractmethod
    def get_config_value(self, section: str, key: str, default: Any = None) -> Any:
        """Get configuration value from printer config"""
        pass

class ConfigParserInterface(ABC):
    """Abstract interface for configuration parsing"""
    
    @abstractmethod
    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """Get configuration value"""
        pass
    
    @abstractmethod
    def has_section(self, section: str) -> bool:
        """Check if configuration section exists"""
        pass

# Mock implementations for development
class MockPrinterManager(PrinterManagerInterface):
    """Mock printer manager for development/testing"""
    
    async def get_printer_status(self):
        """Return mock printer status"""
        return {
            'state': 'ready',
            'print_stats': {'state': 'standby'},
            'toolhead': {'position': [0, 0, 0, 0]},
            'extruder': {'temperature': 22.5},
            'heater_bed': {'temperature': 21.8}
        }
    
    async def send_gcode(self, gcode):
        """Mock gcode sending"""
        logger.info(f"Mock GCode: {gcode}")
        return f"Mock response to: {gcode}"
    
    def get_config_value(self, section, key, default=None):
        """Get config value from real printer.cfg via config parser"""
        # Use the core's config parser
        from ..utils.manager import PrinterBuddyCore
        # This will be improved when we have proper dependency injection
        return default

class MockConfigParser(ConfigParserInterface):
    """Mock config parser that reads actual printer.cfg file"""
    
    def __init__(self):
        self.parser = configparser.ConfigParser()
        # Path to the actual printer.cfg file
        config_path = Path(__file__).parent.parent.parent.parent / "printer.cfg"
        
        try:
            self.parser.read(str(config_path))
            logger.info(f"Loaded config from {config_path}")
        except Exception as e:
            logger.warning(f"Could not load config from {config_path}: {e}")
            self.parser = None
    
    def get(self, section, key, fallback=None):
        """Get config value from actual printer.cfg"""
        if self.parser is None:
            return fallback
        try:
            return self.parser.get(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def has_section(self, section):
        """Check if section exists in actual printer.cfg"""
        if self.parser is None:
            return False
        return self.parser.has_section(section)

# Real hardware implementations (to be implemented)
class MoonrakerPrinterManager(PrinterManagerInterface):
    """Real Moonraker printer manager for hardware communication"""
    
    def __init__(self, moonraker_url="http://localhost:7125"):
        self.moonraker_url = moonraker_url.rstrip('/')  # Remove trailing slash
        logger.info(f"Initialized Moonraker printer manager: {moonraker_url}")
    
    def test_connection(self):
        """Test if Moonraker is reachable - raises exception if not"""
        try:
            # Try to get basic server info with short timeout
            result = self._make_request(f"{self.moonraker_url}/server/info", timeout=5)
            logger.info(f"Moonraker connection test successful: {result.get('result', {}).get('moonraker_version', 'unknown version')}")
            return True
        except Exception as e:
            logger.error(f"Moonraker connection test FAILED: {e}")
            raise Exception(f"Cannot connect to Moonraker at {self.moonraker_url}: {e}")
    
    def _make_request(self, url, data=None, timeout=10):
        """Make HTTP request using standard library urllib"""
        import urllib.request
        import urllib.parse
        import urllib.error
        import json
        import socket
        
        try:
            if data:
                # POST request with JSON data
                data = json.dumps(data).encode('utf-8')
                req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            else:
                # GET request
                req = urllib.request.Request(url)
            
            # Set timeout
            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data)
                
        except (urllib.error.URLError, socket.timeout, json.JSONDecodeError) as e:
            raise Exception(f"HTTP request failed: {e}")
    
    async def get_printer_status(self):
        """Get real printer status from Moonraker API"""
        try:
            # First get basic printer info
            info_data = self._make_request(f"{self.moonraker_url}/printer/info")
            
            # Get detailed printer object status
            status_request = {
                "objects": {
                    "print_stats": None,
                    "toolhead": ["position", "status"],
                    "extruder": ["temperature", "target"],
                    "heater_bed": ["temperature", "target"],
                    "webhooks": ["state", "state_message"]
                }
            }
            
            status_data = self._make_request(f"{self.moonraker_url}/printer/objects/query", status_request)
            
            # Combine and format the data
            combined_status = {
                'state': info_data.get('state', 'unknown'),
                'state_message': info_data.get('state_message', ''),
                'print_stats': status_data.get('status', {}).get('print_stats', {}),
                'toolhead': status_data.get('status', {}).get('toolhead', {}),
                'extruder': status_data.get('status', {}).get('extruder', {}),
                'heater_bed': status_data.get('status', {}).get('heater_bed', {}),
                'webhooks': status_data.get('status', {}).get('webhooks', {}),
                'eventtime': status_data.get('eventtime', 0)
            }
            
            logger.info(f"Retrieved printer status from Moonraker: state={combined_status['state']}")
            return combined_status
            
        except Exception as e:
            logger.error(f"Failed to get printer status from Moonraker: {e}")
            raise
    
    async def send_gcode(self, gcode):
        """Send real gcode command via Moonraker API"""
        try:
            gcode_request = {"script": gcode}
            
            result = self._make_request(f"{self.moonraker_url}/printer/gcode/script", gcode_request)
            
            logger.info(f"GCode '{gcode}' sent to Moonraker successfully")
            return result.get('result', 'ok')
                
        except Exception as e:
            logger.error(f"Failed to send GCode '{gcode}' to Moonraker: {e}")
            raise
    
    def get_config_value(self, section, key, default=None):
        """Get config value from Moonraker processed config (synchronous fallback)"""
        # Note: This is a synchronous method but Moonraker API is async
        # For now, return default - real implementation would need async redesign
        logger.warning(f"Config query for [{section}]{key} not implemented in sync mode")
        return default
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None

class MoonrakerConfigParser(ConfigParserInterface):
    """Real config parser using Moonraker's processed configuration"""
    
    def __init__(self, moonraker_url="http://localhost:7125"):
        self.moonraker_url = moonraker_url.rstrip('/')
        self.session = None
        self._config_cache = {}
        self._cache_time = 0
        self._cache_timeout = 60  # Cache config for 60 seconds
        self._initialized = False
        logger.info(f"Initialized Moonraker config parser: {moonraker_url}")
    
    async def initialize(self):
        """Initialize by fetching config from Moonraker"""
        try:
            self._fetch_config()
            self._initialized = True
            logger.info("MoonrakerConfigParser initialized with processed config")
        except Exception as e:
            logger.warning(f"Failed to initialize MoonrakerConfigParser: {e}, will use fallback")
            self._initialized = False
    
    def _make_request(self, url, data=None, timeout=10):
        """Make HTTP request using standard library urllib"""
        import urllib.request
        import urllib.parse
        import urllib.error
        import json
        import socket
        
        try:
            if data:
                # POST request with JSON data
                data = json.dumps(data).encode('utf-8')
                req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            else:
                # GET request
                req = urllib.request.Request(url)
            
            # Set timeout
            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data)
                
        except (urllib.error.URLError, socket.timeout, json.JSONDecodeError) as e:
            raise Exception(f"HTTP request failed: {e}")
    
    def _fetch_config(self):
        """Fetch configuration from Moonraker"""
        import time
        current_time = time.time()
        
        # Return cached config if still valid
        if (self._config_cache and 
            current_time - self._cache_time < self._cache_timeout):
            return self._config_cache
        
        try:
            # Get printer objects to see what config sections are available
            objects_data = self._make_request(f"{self.moonraker_url}/printer/objects/list")
            
            # Get configfile object which contains the processed config
            config_request = {
                "objects": {
                    "configfile": None  # Get all configfile data
                }
            }
            
            config_data = self._make_request(f"{self.moonraker_url}/printer/objects/query", config_request)
            
            # Extract the config from the response
            configfile = config_data.get('status', {}).get('configfile', {})
            config_dict = configfile.get('config', {}) or configfile.get('settings', {})
            
            # Cache the result
            self._config_cache = config_dict
            self._cache_time = current_time
            
            logger.info(f"Fetched config from Moonraker: {len(config_dict)} sections")
            return config_dict
            
        except Exception as e:
            logger.error(f"Failed to fetch config from Moonraker: {e}")
            # Return empty dict on error, don't raise
            return {}
    
    def get(self, section, key, fallback=None):
        """Get config value from Moonraker processed config (synchronous)"""
        # Since this is a synchronous method but Moonraker is async,
        # we'll fall back to the original approach for now
        # Real implementation would need async redesign of the interface
        
        # Try to use cached config if available
        if self._config_cache and section in self._config_cache:
            section_data = self._config_cache[section]
            if isinstance(section_data, dict) and key in section_data:
                return section_data[key]
        
        # Fall back to reading raw printer.cfg file (same as MockConfigParser)
        try:
            import configparser
            from pathlib import Path
            
            parser = configparser.ConfigParser()
            config_path = Path(__file__).parent.parent.parent.parent / "printer.cfg"
            
            if config_path.exists():
                parser.read(str(config_path))
                return parser.get(section, key, fallback=fallback)
        except:
            pass
            
        logger.debug(f"Config value not found: [{section}]{key}, using fallback: {fallback}")
        return fallback
    
    def has_section(self, section):
        """Check if section exists in Moonraker processed config"""
        # Try cached config first
        if self._config_cache:
            return section in self._config_cache
        
        # Fallback to raw printer.cfg
        try:
            import configparser
            from pathlib import Path
            
            parser = configparser.ConfigParser()
            config_path = Path(__file__).parent.parent.parent.parent / "printer.cfg"
            
            if config_path.exists():
                parser.read(str(config_path))
                return parser.has_section(section)
        except:
            pass
            
        return False
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None

class PrinterBuddyCore:
    """Central Python core managing all business logic and state"""
    
    def __init__(self, hardware_mode="mock", moonraker_url="http://localhost:7125"):
        self.version = "2.0.0"
        self.hardware_mode = hardware_mode
        self.moonraker_url = moonraker_url
        self.modules = {}
        self.state_manager = StateManager()
        self.event_bus = EventBus()
        self.initialized = False
        self.api_server = None
        self.log_messages = []
        self.max_log_messages = 1000
        
        # Create printer manager and config parser based on hardware mode
        if hardware_mode == "real":
            logger.info(f"Initializing with REAL hardware mode (Moonraker: {moonraker_url})")
            self.printer_manager = MoonrakerPrinterManager(moonraker_url)
            self.config_parser = MoonrakerConfigParser(moonraker_url)
            
            # Test connection and set status (don't crash if it fails)
            logger.info("Testing Moonraker connection...")
            try:
                self.printer_manager.test_connection()
                logger.info("Moonraker connection verified - printer operations will be REAL")
                self.connection_status = "connected"
            except Exception as e:
                logger.error("Moonraker connection FAILED")
                logger.error(f"Error: {e}")
                logger.error("Printer operations will FAIL until connection is restored")
                logger.error("Check that:")
                logger.error("   - Moonraker is running on port 7125")
                logger.error("   - Printer is powered on")
                logger.error("   - Network connection is working")
                self.connection_status = "disconnected"
        else:  # mock mode (default)
            logger.info("Initializing with MOCK hardware mode")
            self.printer_manager = MockPrinterManager()
            self.config_parser = MockConfigParser()
            self.connection_status = "mock"
        
        # Set up log message collection for UI
        self._setup_log_collection()
        
        # Initialize core state values
        self.state_manager.set('system.initialized', False)
        self.state_manager.set('system.version', self.version)
        self.state_manager.set('system.start_time', time.time())
        self.state_manager.set('system.hardware_mode', hardware_mode)
        self.state_manager.set('system.moonraker_url', moonraker_url)
        
        logger.info(f"PrinterBuddyCore v{self.version} initialized (mode: {hardware_mode})")
    
    # Module Management
    def register_module(self, module):
        """Register a new module with the core"""
        logger.info(f"Registering module: {module.name}")
        self.modules[module.module_id] = module
        
        # Initialize module state in state manager
        self.state_manager.set(f'modules.{module.module_id}', {
            'name': module.name,
            'status': module.status.value,
            'version': module.version
        })
        
        # Connect module to event bus - check if method exists
        if hasattr(module, 'handle_core_event'):
            self.event_bus.subscribe(f'module_{module.module_id}', module.handle_core_event)
        
        return True
    
    def _setup_log_collection(self):
        """Set up log message collection for UI console"""
        import logging
        
        class UILogHandler(logging.Handler):
            def __init__(self, core_manager):
                super().__init__()
                self.core_manager = core_manager
                
            def emit(self, record):
                try:
                    # Format the log message
                    message = self.format(record)
                    
                    # Determine level for UI
                    level = 'info'
                    if record.levelno >= logging.ERROR:
                        level = 'error'
                    elif record.levelno >= logging.WARNING:
                        level = 'warning'
                    
                    # Add to core manager's log collection
                    self.core_manager.add_log_message(level, message, record.created)
                except Exception:
                    # Don't let logging errors crash the system
                    pass
        
        # Create and add our custom handler
        handler = UILogHandler(self)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # Add to root logger to catch all messages
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
    
    def add_log_message(self, level, message, timestamp):
        """Add a log message for UI consumption"""
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message,
            'source': 'printer_buddy'
        }
        
        self.log_messages.append(log_entry)
        
        # Keep only recent messages
        if len(self.log_messages) > self.max_log_messages:
            self.log_messages = self.log_messages[-self.max_log_messages:]
    
    def get_recent_log_messages(self, since=None):
        """Get recent log messages, optionally filtered by timestamp"""
        if since:
            try:
                since_timestamp = float(since)
                return [msg for msg in self.log_messages if msg['timestamp'] > since_timestamp]
            except (ValueError, TypeError):
                pass
        
        # Return last 50 messages if no since parameter
        return self.log_messages[-50:]
    
    async def _load_core_modules(self):
        """Load essential core modules"""
        try:
            # Load PrinterTestsModule
            if 'printer_tests' not in self.modules:
                from ..modules.printer_tests_module import PrinterTestsModule
                printer_tests_module = PrinterTestsModule(self)
                self.register_module(printer_tests_module)
                logger.info("PrinterTestsModule loaded")
        except ImportError as e:
            logger.warning(f"Could not load PrinterTestsModule: {e}")
        except Exception as e:
            logger.error(f"Error loading core modules: {e}")
    
    async def initialize_all_modules(self):
        """Initialize all registered modules in dependency order"""
        logger.info("Initializing all modules...")
        
        # Initialize config parser if it's a Moonraker parser
        if hasattr(self.config_parser, 'initialize'):
            try:
                await self.config_parser.initialize()
            except Exception as e:
                logger.warning(f"Config parser initialization failed: {e}")
        
        # Load core modules if not already loaded
        await self._load_core_modules()
        
        # TODO: Sort by dependencies
        for name, module in self.modules.items():
            try:
                logger.info(f"Initializing module: {name}")
                await module.initialize()
                logger.info(f"Module {name} initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize module {name}: {e}")
                # Continue with other modules
        
        self.initialized = True
        self.state_manager.set('system.initialized', True)
        logger.info("All modules initialized")
        return True
    
    # Data Flow Management
    def receive_module_update(self, module_name: str, state_update: Dict[str, Any]):
        """Receive state update from a module"""
        logger.debug(f"Received update from {module_name}: {state_update}")
        
        # Update central state
        self.state_manager.update_module_state(module_name, state_update)
        
        # Broadcast to other modules that might need this data
        self.broadcast_state_update(module_name, state_update)
        
        # Notify UI layers if API server is running
        if self.api_server:
            self.api_server.broadcast_state_update(module_name, state_update)
    
    def handle_module_request(self, module_name: str, request: Dict[str, Any]):
        """Handle a request from a module"""
        request_type = request.get('type')
        
        if request_type == 'get_state':
            # Return current state for requested scope
            scope = request.get('scope', 'all')
            return self.get_state(scope)
        
        elif request_type == 'call_module':
            # Call another module's method
            target_module = request.get('target_module')
            method = request.get('method')
            params = request.get('params', {})
            
            if target_module in self.modules:
                target = self.modules[target_module]
                if hasattr(target, method):
                    return getattr(target, method)(**params)
        
        elif request_type == 'emit_event':
            # Emit an event on the event bus
            event_name = request.get('event')
            data = request.get('data', {})
            self.event_bus.emit(event_name, data)
        
        logger.warning(f"Unhandled request from {module_name}: {request}")
        return None
    
    # Event System
    def broadcast_state_update(self, source: str, data: Dict[str, Any]):
        """Broadcast state changes to all interested modules"""
        event_data = {
            'source': source,
            'data': data,
            'timestamp': time.time()
        }
        self.event_bus.emit('state_update', event_data)
    
    # State Access
    def get_state(self, scope: str = 'all') -> Dict[str, Any]:
        """Get current state, optionally filtered by scope"""
        return self.state_manager.get_state(scope)
    
    def get_module_state(self, module_name: str) -> Dict[str, Any]:
        """Get state for a specific module"""
        return self.state_manager.get_module_state(module_name)
    
    # API Server Integration
    def start_api_server(self, port: int = 8080, host: str = '0.0.0.0'):
        """Start HTTP API server for web UI communication"""
        try:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from api.server import PrinterBuddyAPIServer
            self.api_server = PrinterBuddyAPIServer(host, port, self)
            logger.info(f"Starting API server on {host}:{port}")
            self.api_server.start()
            return self.api_server
        except ImportError as e:
            logger.error(f"Could not start API server: {e}")
            return None
    
    # Lifecycle Management
    async def shutdown(self):
        """Graceful shutdown of all modules and services"""
        logger.info("Shutting down PrinterBuddyCore...")
        
        # Shutdown all modules
        for name, module in self.modules.items():
            try:
                await module.shutdown()
                logger.info(f"Module {name} shut down successfully")
            except Exception as e:
                logger.error(f"Error shutting down module {name}: {e}")
        
        # Close printer manager and config parser sessions
        try:
            if hasattr(self.printer_manager, 'close'):
                await self.printer_manager.close()
            if hasattr(self.config_parser, 'close'):
                await self.config_parser.close()
        except Exception as e:
            logger.error(f"Error closing printer manager sessions: {e}")
        
        # Stop API server if running
        if self.api_server and hasattr(self.api_server, 'shutdown'):
            await self.api_server.shutdown()
        
        logger.info("PrinterBuddyCore shutdown complete")
    
    # Utility Methods
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            'version': self.version,
            'initialized': self.initialized,
            'modules': list(self.modules.keys()),
            'uptime': time.time() - self.state_manager.get_state('system')['start_time']
        }

# Main entry point for development/testing
async def main():
    """Main entry point for standalone testing"""
    core = PrinterBuddyCore()
    
    # Load core modules
    from ..modules.config_module import ConfigModule
    from ..modules.status_module import StatusModule
    from ..modules.safety_module import SafetyModule
    
    # Register modules
    core.register_module(ConfigModule('config', core))
    core.register_module(StatusModule('status', core))
    core.register_module(SafetyModule('safety', core))
    
    # Initialize
    await core.initialize_all_modules()
    
    # Start API server
    api_server = core.start_api_server()
    
    logger.info("PrinterBuddy Core running - Press Ctrl+C to exit")
    
    try:
        # Keep running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
        await core.shutdown()

if __name__ == '__main__':
    asyncio.run(main())