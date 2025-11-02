"""
Printer Tests Module for Printer Buddy Core

Handles commissioning and validation tests directly.
Integrates with the core system for state management and event handling.
"""

import logging
import asyncio
import sys
import os
import importlib
import importlib.util
import inspect
import configparser
from pathlib import Path
from typing import Dict, Any, Optional, List, Type

from . import BaseModule, ModuleStatus, ModuleCapability

logger = logging.getLogger(__name__)

class MockPrinterManager:
    """Mock printer manager for testing"""
    
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
        return f"Mock response to: {gcode}"
    
    def get_config_value(self, section, key, default=None):
        """Get config value from real printer.cfg via config parser"""
        config_parser = MockConfigParser()
        return config_parser.get(section, key, fallback=default)

class MockConfigParser:
    """Real config parser that reads actual printer.cfg file"""
    
    def __init__(self):
        self.parser = configparser.ConfigParser()
        # Path to the actual printer.cfg file
        config_path = Path(__file__).parent.parent.parent.parent / "printer.cfg"
        
        try:
            self.parser.read(str(config_path))
            # print(f"DEBUG: Successfully loaded config from {config_path}")
        except Exception as e:
            # print(f"DEBUG: Failed to load config from {config_path}: {e}")
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

class PrinterTestsModule(BaseModule):
    """
    Core module for handling printer commissioning and validation tests
    
    Responsibilities:
    - Integrate test system with core architecture
    - Manage test state through StateManager
    - Publish test events through EventBus
    - Direct test discovery, execution, and monitoring
    """
    
    def __init__(self, core_manager):
        super().__init__('printer_tests', 'Printer Tests Manager', '1.0.0')
        self.core_manager = core_manager
        self.capabilities = [ModuleCapability.COMMISSIONING, ModuleCapability.SAFETY_CRITICAL]
        
        # Test management attributes (formerly in TestManager)
        self.discovered_tests: Dict[str, Type] = {}
        self.running_tests: Dict[str, Any] = {}
        self.test_results: Dict[str, Any] = {}
        
    async def initialize(self) -> bool:
        """Initialize the printer tests module"""
        try:
            self.update_status(ModuleStatus.INITIALIZING)
            logger.info("Initializing Printer Tests Module...")
            
            # Discover tests directly
            self._discover_tests()
            
            # Subscribe to relevant events
            if self.core_manager.event_bus:
                self.core_manager.event_bus.subscribe('commissioning_request', self._handle_commissioning_request)
                self.core_manager.event_bus.subscribe('test_user_response', self._handle_user_response)
            
            # Initialize commissioning state in StateManager
            if self.core_manager.state_manager:
                self.core_manager.state_manager.set('commissioning.active', False)
                self.core_manager.state_manager.set('commissioning.current_test', None)
                self.core_manager.state_manager.set('commissioning.available_tests', self._get_available_tests())
            
            self.update_status(ModuleStatus.READY)
            logger.info("Printer Tests Module initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Printer Tests Module: {e}")
            self.update_status(ModuleStatus.ERROR)
            return False
    
    def _discover_tests(self) -> List[Dict[str, Any]]:
        """
        Dynamically discover all test classes in the printer_tests directory
        Returns list of test metadata for the API
        """
        self.discovered_tests.clear()
        tests_metadata = []
        
        try:
            # Add printer_tests directory to path
            printer_tests_path = Path(__file__).parent.parent.parent / 'printer_tests'
            # logger.info(f"DEBUG: Looking for tests in: {printer_tests_path}")
            # logger.info(f"DEBUG: Path exists: {printer_tests_path.exists()}")
            
            if str(printer_tests_path) not in sys.path:
                sys.path.insert(0, str(printer_tests_path))
            
            # Import BaseTest and TestStatus
            from base_test import BaseTest, TestStatus
            # logger.info("DEBUG: Successfully imported BaseTest and TestStatus")
            
            # Get all .py files in printer_tests directory (except specific files)
            test_files = [
                f for f in os.listdir(printer_tests_path) 
                if f.endswith('.py') and f not in ['__init__.py', 'base_test.py']
            ]
            # logger.info(f"DEBUG: Found test files: {test_files}")
            
            for test_file in test_files:
                try:
                    # Import the module
                    module_name = test_file[:-3]  # Remove .py extension
                    # logger.info(f"DEBUG: Attempting to import module: {module_name}")
                    module = importlib.import_module(module_name)
                    # logger.info(f"DEBUG: Successfully imported module: {module_name}")
                    
                    # Get BaseTest from the module to ensure we're using the same class reference
                    module_BaseTest = getattr(module, 'BaseTest', None)
                    if not module_BaseTest:
                        # logger.info(f"DEBUG: Module {module_name} doesn't have BaseTest, skipping")
                        continue
                    
                    # Find classes that inherit from BaseTest
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        # logger.info(f"DEBUG: Found class {name} in {module_name}, module={obj.__module__}")
                        
                        # Use the module's BaseTest reference for comparison
                        if (obj != module_BaseTest and 
                            issubclass(obj, module_BaseTest) and 
                            obj.__module__ == module_name):
                            
                            # logger.info(f"DEBUG: Found valid test class: {name}")
                            # Get test metadata
                            test_id = module_name
                            test_metadata = {
                                'id': test_id,
                                'name': obj.get_name(),
                                'description': obj.get_description(),
                                'category': getattr(obj, 'category', 'general'),
                                'estimated_time': getattr(obj, 'estimated_time', '2-5 minutes'),
                                'dependencies': obj.get_dependencies()
                            }
                            
                            # Store the class for later instantiation
                            self.discovered_tests[test_id] = obj
                            tests_metadata.append(test_metadata)
                            
                            logger.info(f"Discovered test: {test_metadata['name']} ({test_id})")
                            break
                            
                except Exception as e:
                    logger.error(f"Error loading test module {test_file}: {e}")
                    # import traceback
                    # logger.error(f"DEBUG: Full traceback: {traceback.format_exc()}")
                    continue
            
            # Sort tests by dependencies (tests with no dependencies first)
            tests_metadata.sort(key=lambda x: len(x['dependencies']))
            
            logger.info(f"Discovered {len(tests_metadata)} tests")
            return tests_metadata
            
        except Exception as e:
            logger.error(f"Error discovering tests: {e}")
            return []
    
    def _get_available_tests(self) -> list:
        """Get list of available tests (returns cached results if already discovered)"""
        if not self.discovered_tests:
            # Only run discovery if we haven't discovered tests yet
            self._discover_tests()
        
        # Return cached test info
        tests = []
        for test_id, test_class in self.discovered_tests.items():
            tests.append({
                'id': test_id,
                'name': test_class.get_name(),
                'description': test_class.get_description(),
                'category': getattr(test_class, 'category', 'general'),
                'estimated_time': getattr(test_class, 'estimated_time', '2-5 minutes'),
                'dependencies': test_class.get_dependencies(),
                'status': self._get_test_status(test_id)
            })
        
        return tests
    
    def _get_test_status(self, test_id: str) -> str:
        """Get current status of a test"""
        # Import here to avoid circular imports
        try:
            from base_test import TestStatus
        except ImportError:
            TestStatus = None
            
        # Look for running test with this test_id
        for run_id, test_instance in self.running_tests.items():
            if hasattr(test_instance, 'test_id') and test_instance.test_id == test_id:
                return test_instance.status
        
        # Check completed test results
        if test_id in self.test_results:
            return self.test_results[test_id]['status']
        else:
            return 'not_started' if TestStatus is None else TestStatus.NOT_STARTED
    
    def _progress_callback(self, run_id: str, progress: int, message: str = ""):
        """Callback for test progress updates"""
        logger.info(f"Test progress: {progress}% - {message}")
        # Integrate with core system
        if self.core_manager and hasattr(self.core_manager, 'event_bus') and self.core_manager.event_bus:
            self.core_manager.event_bus.publish('test_progress', 'printer_tests', {
                'run_id': run_id, 'progress': progress, 'message': message
            })
    
    def _status_callback(self, run_id: str, status: str, message: str = ""):
        """Callback for test status updates"""
        logger.info(f"Test status changed: {status} - {message}")
        # Integrate with core system
        if self.core_manager and hasattr(self.core_manager, 'event_bus') and self.core_manager.event_bus:
            self.core_manager.event_bus.publish('test_status', 'printer_tests', {
                'run_id': run_id, 'status': status, 'message': message
            })
    
    def _user_prompt_callback(self, run_id: str, prompt_data: Dict[str, Any]):
        """Callback for user prompts"""
        logger.info(f"Test requesting user input: {prompt_data}")
        # Integrate with core system
        if self.core_manager and hasattr(self.core_manager, 'event_bus') and self.core_manager.event_bus:
            self.core_manager.event_bus.publish('test_user_prompt', 'printer_tests', {
                'run_id': run_id, 'prompt_data': prompt_data
            })
    
    async def start_test(self, test_id: str) -> Dict[str, Any]:
        """Start a commissioning test"""
        try:
            if test_id not in self.discovered_tests:
                return {'success': False, 'error': f'Test not found: {test_id}'}
            
            # Check if any instance of this test_id is already running
            for run_id, test_instance in self.running_tests.items():
                if hasattr(test_instance, 'test_id') and test_instance.test_id == test_id:
                    return {'success': False, 'error': f'Test already running: {test_id} (run_id: {run_id})'}
            
            # Update state
            if self.core_manager.state_manager:
                self.core_manager.state_manager.set('commissioning.active', True)
                self.core_manager.state_manager.set('commissioning.current_test', test_id)
            
            # Create test instance with proper parameters
            test_class = self.discovered_tests[test_id]
            
            # Get printer manager and config parser from core manager
            printer_manager = self.core_manager.printer_manager
            config_parser = self.core_manager.config_parser
            
            # Generate run ID
            run_id = f"{test_id}_{int(asyncio.get_event_loop().time())}"
            
            # Create wrapper callbacks that include run_id
            def progress_wrapper(progress: int, message: str = ""):
                self._progress_callback(run_id, progress, message)
            
            def status_wrapper(status: str, message: str = ""):
                self._status_callback(run_id, status, message)
            
            def user_prompt_wrapper(prompt_data: Dict[str, Any]):
                self._user_prompt_callback(run_id, prompt_data)
            
            test_instance = test_class(
                printer_manager=printer_manager,
                config_parser=config_parser,
                progress_callback=progress_wrapper,
                status_callback=status_wrapper,
                user_prompt_callback=user_prompt_wrapper
            )
            
            # Add run_id and test_id to test instance for reference
            test_instance.run_id = run_id
            test_instance.test_id = test_id
            
            # Store running test
            self.running_tests[run_id] = test_instance
            
            # Start test execution in background
            asyncio.create_task(self._execute_test(run_id, test_instance))
            
            # Publish event
            if self.core_manager.event_bus:
                self.core_manager.event_bus.publish(
                    'test_started', 
                    'printer_tests',
                    {'test_id': test_id, 'run_id': run_id},
                    priority=1
                )
            
            return {
                'success': True,
                'run_id': run_id,
                'test_id': test_id,
                'status': 'running',
                'message': f'Starting {test_class.get_name()}...'
            }
            
        except Exception as e:
            logger.error(f"Failed to start test {test_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _execute_test(self, run_id: str, test_instance):
        """Execute a test in the background"""
        try:
            logger.info(f"Starting execution of test {run_id}")
            result = await test_instance.run()
            logger.info(f"Test {run_id} completed with result: {result}")
            
            # Store result
            self.test_results[run_id] = {
                'run_id': run_id,
                'test_id': test_instance.test_id,
                'status': result['status'],
                'result': result,
                'completed_at': asyncio.get_event_loop().time()
            }
            
            # Remove from running tests
            if run_id in self.running_tests:
                del self.running_tests[run_id]
                
        except Exception as e:
            logger.error(f"Error executing test {run_id}: {e}")
            
            # Store error result
            self.test_results[run_id] = {
                'run_id': run_id,
                'test_id': getattr(test_instance, 'test_id', 'unknown'),
                'status': 'error',
                'error': str(e),
                'completed_at': asyncio.get_event_loop().time()
            }
            
            # Remove from running tests
            if run_id in self.running_tests:
                del self.running_tests[run_id]
    
    def start_test_sync(self, test_id: str) -> Dict[str, Any]:
        """Synchronous wrapper for start_test"""
        import asyncio
        import threading
        
        try:
            # Get the current event loop if it exists
            try:
                loop = asyncio.get_running_loop()
                # We're in an event loop, need to run in a thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_start_test_in_thread, test_id)
                    return future.result(timeout=10)  # 10 second timeout
            except RuntimeError:
                # No event loop, we can run directly
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self.start_test(test_id))
                finally:
                    loop.close()
                    
        except Exception as e:
            logger.error(f"Error in start_test_sync: {e}")
            return {'success': False, 'error': str(e)}
    
    def _run_start_test_in_thread(self, test_id: str) -> Dict[str, Any]:
        """Helper to run start_test in a new thread with its own event loop"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.start_test(test_id))
        finally:
            loop.close()
    
    def get_test_status_by_run_id(self, run_id: str) -> Dict[str, Any]:
        """Get full test status including prompt data by run_id"""
        try:
            # Get test instance directly by run_id (since run_id is the key)
            test_instance = self.running_tests.get(run_id)
            
            if not test_instance:
                # Try to find in completed results
                if run_id in self.test_results:
                    result = self.test_results[run_id]
                    return {
                        'status': result['status'],
                        'message': result.get('message', ''),
                        'progress': 100 if result['status'] in ['passed', 'failed'] else 0,
                        'run_id': run_id
                    }
                
                return {
                    'status': 'not_found',
                    'message': f'Test run not found: {run_id}',
                    'error': 'Test run not found'
                }
            
            # Get current status
            status_data = {
                'status': test_instance.status,
                'message': getattr(test_instance, 'error_message', '') or 'Running...',
                'progress': test_instance.progress,
                'run_id': run_id
            }
            
            # Add prompt data if test is waiting for user
            if hasattr(test_instance, 'status') and test_instance.status == 'waiting_user':
                if hasattr(test_instance, 'pending_prompt') and test_instance.pending_prompt:
                    status_data['prompt'] = test_instance.pending_prompt
            
            return status_data
            
        except Exception as e:
            logger.error(f"Error getting test status for run_id {run_id}: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'error': str(e)
            }
    
    def get_test_ui_config(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get UI configuration for a test (running or available)"""
        logger.info(f"PrinterTestsModule.get_test_ui_config() called with test_id: '{test_id}'")
        
        try:
            # First, look for running test instance with this test_id
            logger.info(f"Checking {len(self.running_tests)} running tests...")
            for run_id, test_instance in self.running_tests.items():
                if hasattr(test_instance, '__class__') and test_instance.__class__.__name__.lower().startswith(test_id.lower()):
                    logger.info(f"Found running test: {test_instance.__class__.__name__}")
                    # Check if test has get_ui_config method
                    if hasattr(test_instance, 'get_ui_config'):
                        ui_config = test_instance.get_ui_config()
                        if ui_config:
                            ui_config['run_id'] = run_id
                            ui_config['test_status'] = 'running'
                            logger.info("Returning UI config for running test")
                            return ui_config
            
            # If no running test found, create a temporary instance to get UI config
            logger.info(f"Checking {len(self.discovered_tests)} discovered tests...")
            for discovered_test_id, test_class in self.discovered_tests.items():
                logger.info(f"Checking discovered test_id: '{discovered_test_id}' against requested test_id: '{test_id}'")
                if discovered_test_id == test_id:
                    logger.info(f"Match found! Creating temp instance of {test_class.__name__}")
                    try:
                        # Create temporary instance just to get UI config (same as start_test method)
                        printer_manager = self.core_manager.printer_manager
                        config_parser = self.core_manager.config_parser
                        temp_instance = test_class(
                            printer_manager=printer_manager, 
                            config_parser=config_parser,
                            progress_callback=lambda p, m: None,  # Dummy callbacks
                            status_callback=lambda s, m: None,
                            user_prompt_callback=lambda d: None
                        )
                        
                        if hasattr(temp_instance, 'get_ui_config'):
                            logger.info("Calling get_ui_config() on temp instance")
                            ui_config = temp_instance.get_ui_config()
                            if ui_config:
                                ui_config['test_status'] = 'available'
                                logger.info("Returning UI config for available test")
                                return ui_config
                        else:
                            logger.warning(f"Test {test_class.__name__} does not have get_ui_config method")
                    except Exception as e:
                        logger.warning(f"Could not create temp instance of {test_class.__name__}: {e}")
                        continue
            
            logger.warning(f"No UI config found for test_id: {test_id}")
            return None
        
        except Exception as e:
            logger.error(f"Error getting UI config for {test_id}: {e}")
            return None
    
    def submit_user_response_sync(self, run_id: str, response: Any) -> Dict[str, Any]:
        """Send user response to a waiting test (synchronous version)"""
        try:
            if run_id not in self.running_tests:
                return {'success': False, 'error': f"No active test found for run_id: {run_id}"}
            
            test = self.running_tests[run_id]
            if not hasattr(test, 'status') or test.status != 'waiting_user':
                return {'success': False, 'error': f"Test {run_id} is not waiting for user input"}
            
            # Send response to test directly
            if hasattr(test, 'submit_user_response'):
                test.submit_user_response({'response': response})
            
            return {
                'success': True,
                'run_id': run_id,
                'status': 'acknowledged',
                'message': f'Response "{response}" received and processed.'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # REMOVED: Dead methods that referenced self.test_manager
    # These are replaced by the direct implementations above
    
    def _handle_test_progress(self, run_id: str, progress: int, message: str):
        """Handle test progress updates from TestManager"""
        # Update state
        if self.core_manager.state_manager:
            self.core_manager.state_manager.set('commissioning.progress', progress)
            self.core_manager.state_manager.set('commissioning.current_message', message)
        
        # Publish event
        if self.core_manager.event_bus:
            self.core_manager.event_bus.publish(
                'test_progress',
                'printer_tests',
                {'run_id': run_id, 'progress': progress, 'message': message}
            )
        
        logger.info(f"Test {run_id} progress: {progress}% - {message}")
    
    def _handle_test_status(self, run_id: str, status: str, message: str):
        """Handle test status updates from TestManager"""
        # Update state
        if self.core_manager.state_manager:
            self.core_manager.state_manager.set('commissioning.status', status)
            self.core_manager.state_manager.set('commissioning.status_message', message)
            
            # If test completed, clear active state
            if status in ['passed', 'failed', 'error']:
                self.core_manager.state_manager.set('commissioning.active', False)
                self.core_manager.state_manager.set('commissioning.current_test', None)
        
        # Publish event
        if self.core_manager.event_bus:
            self.core_manager.event_bus.publish(
                'test_status_changed',
                'printer_tests',
                {'run_id': run_id, 'status': status, 'message': message},
                priority=2 if status in ['failed', 'error'] else 1
            )
        
        logger.info(f"Test {run_id} status: {status} - {message}")
    
    def _handle_user_prompt(self, run_id: str, prompt_data: Dict[str, Any]):
        """Handle user prompts from TestManager"""
        # Update state
        if self.core_manager.state_manager:
            self.core_manager.state_manager.set('commissioning.user_prompt', prompt_data)
        
        # Publish event for UI to handle
        if self.core_manager.event_bus:
            self.core_manager.event_bus.publish(
                'test_user_prompt',
                'printer_tests',
                {'run_id': run_id, 'prompt': prompt_data},
                priority=3  # High priority for user interaction
            )
        
        logger.info(f"Test {run_id} user prompt: {prompt_data.get('message', 'No message')}")
    
    def _handle_commissioning_request(self, event):
        """Handle commissioning request events"""
        request_type = event.data.get('type')
        
        if request_type == 'start_test':
            test_id = event.data.get('test_id')
            asyncio.create_task(self.start_test(test_id))
        elif request_type == 'get_status':
            run_id = event.data.get('run_id')
            asyncio.create_task(self.get_test_status(run_id))
        elif request_type == 'user_response':
            run_id = event.data.get('run_id')
            response = event.data.get('response')
            asyncio.create_task(self.submit_user_response(run_id, response))
    
    def _handle_user_response(self, event):
        """Handle user response events"""
        run_id = event.data.get('run_id')
        response = event.data.get('response')
        if run_id and response is not None:
            asyncio.create_task(self.submit_user_response(run_id, response))
    
    async def shutdown(self):
        """Shutdown the printer tests module"""
        # Stop any running tests
        for run_id in list(self.running_tests.keys()):
            try:
                test_instance = self.running_tests[run_id]
                if hasattr(test_instance, 'cleanup'):
                    await test_instance.cleanup()
                del self.running_tests[run_id]
            except Exception as e:
                logger.error(f"Error stopping test {run_id}: {e}")
        
        # Clear state
        if self.core_manager.state_manager:
            self.core_manager.state_manager.set('commissioning.active', False)
            self.core_manager.state_manager.set('commissioning.current_test', None)
        
        self.update_status(ModuleStatus.DISABLED)
        logger.info("Printer Tests Module shutdown")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current module status"""
        status = {
            'module_id': self.module_id,
            'name': self.name,
            'status': self.status.value,
            'discovered_tests_count': len(self.discovered_tests),
            'running_tests_count': len(self.running_tests),
            'available_tests': self._get_available_tests()
        }
        
        # Add commissioning state if available
        if self.core_manager.state_manager:
            commissioning_state = self.core_manager.state_manager.get('commissioning', {})
            status['commissioning'] = commissioning_state
        
        return status