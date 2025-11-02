"""
API Server for Printer Buddy Core

HTTP REST API server for web UI communication.
"""

import asyncio
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional
import threading
from datetime import datetime

# Using built-in http.server for minimal dependencies
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import socketserver

logger = logging.getLogger(__name__)

class PrinterBuddyAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Printer Buddy API"""
    
    def __init__(self, *args, core_manager=None, **kwargs):
        self.core_manager = core_manager
        super().__init__(*args, **kwargs)
        
    def do_GET(self):
        """Handle GET requests"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)
            
            # Route the request
            if path == '/api/status':
                self._handle_status()
            elif path == '/api/state':
                self._handle_get_state(query_params)
            elif path == '/api/modules':
                self._handle_get_modules()
            elif path == '/api/config':
                self._handle_get_config()
            elif path == '/api/commissioning/tests':
                self._handle_get_available_tests()
            elif path == '/api/commissioning/status':
                self._handle_get_commissioning_status(query_params)
            elif path.startswith('/api/commissioning/ui-config/'):
                test_id = path.split('/')[-1]
                self._handle_get_ui_config(test_id)
            elif path == '/api/logs/list':
                self._handle_get_logs_list()
            elif path == '/api/logs/stream':
                self._handle_get_logs_stream(query_params)
            elif path.startswith('/api/'):
                self._send_json_response({'error': 'API endpoint not found'}, 404)
            else:
                # Serve static files
                self._serve_static_file(path)
                
        except Exception as e:
            logger.error(f"Error handling GET {self.path}: {e}")
            self._send_json_response({'error': 'Internal server error'}, 500)
            
    def do_POST(self):
        """Handle POST requests"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_json_response({'error': 'Invalid JSON'}, 400)
                return
                
            # Route the request
            if path == '/api/command':
                self._handle_command(data)
            elif path == '/api/gcode':
                self._handle_command(data)  # Same handler as /api/command
            elif path == '/api/state':
                self._handle_set_state(data)
            elif path == '/api/emergency_stop':
                self._handle_emergency_stop()
            elif path == '/api/commissioning/start':
                self._handle_start_commissioning(data)
            elif path == '/api/commissioning/stop':
                self._handle_stop_commissioning()
            elif path == '/api/commissioning/respond':
                self._handle_commissioning_respond(data)
            else:
                self._send_json_response({'error': 'API endpoint not found'}, 404)
                
        except Exception as e:
            logger.error(f"Error handling POST {self.path}: {e}")
            self._send_json_response({'error': 'Internal server error'}, 500)
            
    def _handle_status(self):
        """Handle /api/status request"""
        if not self.core_manager:
            self._send_json_response({'error': 'Core manager not available'}, 503)
            return
            
        status = {
            'timestamp': datetime.now().isoformat(),
            'system_status': 'ready',
            'modules': {},
            'emergency_stop': False,
            'hardware_mode': getattr(self.core_manager, 'hardware_mode', 'unknown'),
            'connection_status': getattr(self.core_manager, 'connection_status', 'unknown'),
            'moonraker_url': getattr(self.core_manager, 'moonraker_url', None) if hasattr(self.core_manager, 'hardware_mode') and self.core_manager.hardware_mode == 'real' else None
        }
        
        # Add placeholder printer data based on connection status
        connection_status = getattr(self.core_manager, 'connection_status', 'unknown')
        logger.info(f"API Status: connection_status = {connection_status}")
        if connection_status == 'connected':
            # TODO: Get real printer data from async background task
            status['temperatures'] = {
                'bed': 0,
                'bed_target': 0,  
                'extruder': 0,
                'extruder_target': 0
            }
            status['position'] = {
                'x': 0,
                'y': 0,
                'z': 0
            }
        else:
            # Return null/empty data when disconnected
            status['temperatures'] = {
                'bed': None,
                'bed_target': None,
                'extruder': None, 
                'extruder_target': None
            }
            status['position'] = {
                'x': None,
                'y': None,
                'z': None
            }
        
        # Get status from core manager  
        if hasattr(self.core_manager, 'get_system_status'):
            status.update(self.core_manager.get_system_status())
            
        self._send_json_response(status)
        
    def _handle_get_state(self, query_params):
        """Handle /api/state GET request"""
        if not self.core_manager or not self.core_manager.state_manager:
            self._send_json_response({'error': 'State manager not available'}, 503)
            return
            
        # Get specific key or all state
        key = query_params.get('key', [None])[0]
        
        if key:
            value = self.core_manager.state_manager.get(key)
            response = {'key': key, 'value': value}
        else:
            response = self.core_manager.state_manager.get_all()
            
        self._send_json_response(response)
        
    def _handle_set_state(self, data):
        """Handle /api/state POST request"""
        if not self.core_manager or not self.core_manager.state_manager:
            self._send_json_response({'error': 'State manager not available'}, 503)
            return
            
        try:
            key = data.get('key')
            value = data.get('value')
            
            if not key:
                self._send_json_response({'error': 'Key required'}, 400)
                return
                
            self.core_manager.state_manager.set(key, value)
            self._send_json_response({'success': True, 'key': key, 'value': value})
            
        except Exception as e:
            self._send_json_response({'error': str(e)}, 400)
            
    def _handle_get_modules(self):
        """Handle /api/modules request"""
        if not self.core_manager:
            self._send_json_response({'error': 'Core manager not available'}, 503)
            return
            
        modules = {}
        if hasattr(self.core_manager, 'modules'):
            for module_id, module in self.core_manager.modules.items():
                modules[module_id] = {
                    'name': module.name,
                    'version': module.version,
                    'status': module.status.value,
                    'capabilities': [cap.value for cap in module.capabilities]
                }
                
        self._send_json_response({'modules': modules})
        
    def _handle_get_config(self):
        """Handle /api/config request"""
        # Return configuration info
        config = {
            'version': '2.0.0',
            'features': ['safety', 'commissioning', 'monitoring'],
            'ui_config': {
                'panels': ['status', 'commissioning', 'logs'],
                'theme': 'dark'
            }
        }
        
        self._send_json_response(config)
        
    def _handle_command(self, data):
        """Handle /api/command request"""
        command = data.get('command')
        
        if not command:
            self._send_json_response({'error': 'Command required'}, 400)
            return
            
        # Send G-code command through printer manager
        try:
            if self.core_manager and hasattr(self.core_manager, 'printer_manager'):
                # Use asyncio to run the async method in the HTTP thread
                import asyncio
                try:
                    # Create a new event loop for this thread
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        # No event loop in this thread, create one
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    result = loop.run_until_complete(self.core_manager.printer_manager.send_gcode(command))
                    self._send_json_response({
                        'success': True, 
                        'result': result,
                        'command': command
                    })
                except Exception as async_error:
                    self._send_json_response({
                        'success': False,
                        'error': f'G-code execution failed: {async_error}',
                        'command': command
                    })
            else:
                self._send_json_response({'error': 'Printer manager not available'}, 503)
                
        except Exception as e:
            self._send_json_response({'error': str(e)}, 500)
            
    def _handle_emergency_stop(self):
        """Handle /api/emergency_stop request"""
        if self.core_manager and self.core_manager.state_manager:
            self.core_manager.state_manager.emergency_stop()
            self._send_json_response({'success': True, 'message': 'Emergency stop activated'})
        else:
            self._send_json_response({'error': 'Emergency stop not available'}, 503)
            
    def _handle_start_commissioning(self, data):
        """Handle /api/commissioning/start request"""
        test_id = data.get('test_id')
        
        if not test_id:
            self._send_json_response({'error': 'test_id required'}, 400)
            return
        
        # Get PrinterTestsModule
        printer_tests_module = self._get_printer_tests_module()
        if not printer_tests_module:
            self._send_json_response({'error': 'Printer tests module not available'}, 503)
            return
        
        try:
            # Use the synchronous start method that we added
            result = printer_tests_module.start_test_sync(test_id)
            
            if result and result.get('run_id'):
                response = {
                    'success': True,
                    'message': f'Starting test: {test_id}',
                    'test_id': test_id,
                    'run_id': result['run_id']
                }
                logger.info(f"Test {test_id} started successfully with run_id: {result['run_id']}")
            else:
                response = {
                    'success': False,
                    'error': 'Failed to start test - no run_id returned',
                    'test_id': test_id
                }
                logger.error(f"Failed to start test {test_id}: no run_id in result")
                
        except Exception as e:
            logger.error(f"Error in _handle_start_commissioning: {e}")
            response = {
                'success': False,
                'error': f'Error starting test: {str(e)}',
                'test_id': test_id
            }
        
        self._send_json_response(response)
        
    def _handle_stop_commissioning(self):
        """Handle /api/commissioning/stop request"""
        # Get PrinterTestsModule
        printer_tests_module = self._get_printer_tests_module()
        if not printer_tests_module:
            self._send_json_response({'error': 'Printer tests module not available'}, 503)
            return
        
        # Update state to stop commissioning
        if self.core_manager and self.core_manager.state_manager:
            self.core_manager.state_manager.set('commissioning.active', False)
            self.core_manager.state_manager.set('commissioning.current_test', None)
        
        response = {
            'success': True,
            'message': 'Commissioning stopped'
        }
        
        self._send_json_response(response)
    
    def _handle_get_available_tests(self):
        """Handle /api/commissioning/tests request"""
        printer_tests_module = self._get_printer_tests_module()
        if not printer_tests_module:
            self._send_json_response({'error': 'Printer tests module not available'}, 503)
            return
        
        tests = printer_tests_module._get_available_tests()
        self._send_json_response({'tests': tests})
    
    def _handle_get_ui_config(self, test_id):
        """Handle /api/commissioning/ui-config/<test_id> request"""
        logger.info(f"API: Received UI config request for test_id: '{test_id}'")
        
        printer_tests_module = self._get_printer_tests_module()
        if not printer_tests_module:
            logger.error("API: Printer tests module not available")
            self._send_json_response({'error': 'Printer tests module not available'}, 503)
            return
        
        try:
            # Find the running test with this test_id
            logger.info(f"API: Calling printer_tests_module.get_test_ui_config('{test_id}')")
            ui_config = printer_tests_module.get_test_ui_config(test_id)
            if ui_config:
                logger.info(f"API: UI config found, sending response with {len(ui_config)} keys")
                self._send_json_response(ui_config)
            else:
                logger.warning(f"API: No UI config available for test {test_id}")
                self._send_json_response({'error': f'No UI config available for test {test_id}'}, 404)
        except Exception as e:
            logger.error(f"API: Error getting UI config for {test_id}: {e}")
            self._send_json_response({'error': str(e)}, 500)
    
    def _handle_get_commissioning_status(self, query_params):
        """Handle /api/commissioning/status request"""
        run_id = query_params.get('run_id', [None])[0]
        
        printer_tests_module = self._get_printer_tests_module()
        if not printer_tests_module:
            self._send_json_response({'error': 'Printer tests module not available'}, 503)
            return
        
        if run_id:
            # Get specific test status from TestManager
            try:
                # Use the direct synchronous method
                status = printer_tests_module.get_test_status_by_run_id(run_id)
                self._send_json_response(status)
            except Exception as e:
                logger.error(f"Error getting test status for {run_id}: {e}")
                self._send_json_response({'error': str(e)}, 500)
        else:
            # Get general commissioning status
            if self.core_manager and self.core_manager.state_manager:
                commissioning_state = self.core_manager.state_manager.get('commissioning', {})
                self._send_json_response(commissioning_state)
            else:
                self._send_json_response({'error': 'State manager not available'})
    
    def _handle_commissioning_respond(self, data):
        """Handle /api/commissioning/respond request"""
        run_id = data.get('run_id')
        response = data.get('response')
        
        if not run_id or response is None:
            self._send_json_response({'error': 'run_id and response required'}, 400)
            return
        
        printer_tests_module = self._get_printer_tests_module()
        if not printer_tests_module:
            self._send_json_response({'error': 'Printer tests module not available'}, 503)
            return
        
        # Submit response directly (synchronous)
        try:
            result = printer_tests_module.submit_user_response_sync(run_id, response)
            logger.info(f"User response submitted for {run_id}: {result}")
        except Exception as e:
            logger.error(f"Error submitting response for {run_id}: {e}")
        
        response_data = {
            'success': True,
            'message': 'Response submitted'
        }
        
        self._send_json_response(response_data)
    
    def _get_printer_tests_module(self):
        """Get the PrinterTestsModule from core manager"""
        if self.core_manager and hasattr(self.core_manager, 'modules'):
            return self.core_manager.modules.get('printer_tests')
        return None
    
    def _serve_static_file(self, path):
        """Serve static web files"""
        if path == '/':
            path = '/index.html'
            
        # Map to web directory
        web_root = Path(__file__).parent.parent / 'web'
        file_path = web_root / path.lstrip('/')
        
        if file_path.exists() and file_path.is_file():
            # Determine content type
            content_type = 'text/html'
            if file_path.suffix == '.js':
                content_type = 'application/javascript'
            elif file_path.suffix == '.css':
                content_type = 'text/css'
            elif file_path.suffix == '.json':
                content_type = 'application/json'
                
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                    
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(content)))
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                import time
                self.send_header('ETag', f'"{int(time.time())}"')  # Force refresh
                self.end_headers()
                self.wfile.write(content)
                
            except Exception as e:
                logger.error(f"Error serving file {file_path}: {e}")
                self._send_json_response({'error': 'File read error'}, 500)
        else:
            logger.warning(f"File not found: {file_path}")
            self._send_json_response({'error': 'File not found'}, 404)
    
    def _handle_get_logs_list(self):
        """Handle /api/logs/list request"""
        # Return available log files
        logs = {
            'files': [
                {
                    'name': 'System Log',
                    'path': 'system.log',
                    'size': 1024,
                    'modified': datetime.now().isoformat()
                }
            ]
        }
        self._send_json_response({'success': True, 'files': logs['files']})
    
    def _handle_get_logs_stream(self, query_params):
        """Handle /api/logs/stream request - return recent log messages for console"""
        since = query_params.get('since', [None])[0]
        
        # Get recent log messages from core manager
        if self.core_manager and hasattr(self.core_manager, 'get_recent_log_messages'):
            messages = self.core_manager.get_recent_log_messages(since)
        else:
            # Return empty if no log system
            messages = []
        
        self._send_json_response({'messages': messages})
        
    def _serve_static_file(self, path):
        """Serve static web files"""
        if path == '/':
            path = '/index.html'
            
        # Map to web directory
        web_root = Path(__file__).parent.parent / 'web'
        file_path = web_root / path.lstrip('/')
        
        if file_path.exists() and file_path.is_file():
            # Determine content type
            content_type = 'text/html'
            if file_path.suffix == '.js':
                content_type = 'application/javascript'
            elif file_path.suffix == '.css':
                content_type = 'text/css'
            elif file_path.suffix == '.json':
                content_type = 'application/json'
                
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                    
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                
            except Exception as e:
                logger.error(f"Error serving file {file_path}: {e}")
                self._send_json_response({'error': 'File read error'}, 500)
        else:
            self._send_json_response({'error': 'File not found'}, 404)
            
    def _send_json_response(self, data, status_code=200):
        """Send JSON response"""
        json_data = json.dumps(data, indent=2)
        
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(json_data)))
        self.end_headers()
        self.wfile.write(json_data.encode('utf-8'))
        
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.debug(f"HTTP: {format % args}")

class PrinterBuddyAPIServer:
    """HTTP API Server for Printer Buddy"""
    
    def __init__(self, host='localhost', port=8080, core_manager=None):
        self.host = host
        self.port = port
        self.core_manager = core_manager
        self.server = None
        self.server_thread = None
        
    def start(self):
        """Start the API server"""
        try:
            # Create handler class with core manager
            handler_class = lambda *args, **kwargs: PrinterBuddyAPIHandler(
                *args, core_manager=self.core_manager, **kwargs
            )
            
            self.server = HTTPServer((self.host, self.port), handler_class)
            
            # Start server in separate thread
            self.server_thread = threading.Thread(
                target=self.server.serve_forever,
                daemon=True
            )
            self.server_thread.start()
            
            logger.info(f"API server started on http://{self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Failed to start API server: {e}")
            raise
            
    def stop(self):
        """Stop the API server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            
        if self.server_thread:
            self.server_thread.join(timeout=5)
            
        logger.info("API server stopped")