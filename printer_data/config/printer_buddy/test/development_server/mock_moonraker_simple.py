#!/usr/bin/env python3
"""
Mock Moonraker Server for Development

This server provides only basic Moonraker-compatible endpoints for development testing.
It does NOT handle test orchestration - that's handled by the core PrinterBuddy system.

Provides:
- Basic printer status data
- Temperature readings
- Position information
- Print statistics
- Log access

Does NOT provide:
- Test management
- Commissioning logic
- Business logic of any kind
"""

import json
import time
import logging
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockMoonrakerHandler(BaseHTTPRequestHandler):
    """HTTP request handler for mock Moonraker API"""
    
    def __init__(self, *args, **kwargs):
        self.mock_data_dir = Path(__file__).parent / '..' / 'mock_data'
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            # Route requests to appropriate handlers
            if path == '/api/printer/info':
                self._handle_printer_info()
            elif path == '/api/printer/objects/query':
                self._handle_printer_objects_query()
            elif path == '/server/info':
                self._handle_server_info()
            elif path == '/server/config':
                self._handle_server_config()
            elif path == '/api/server/files/list':
                self._handle_files_list()
            elif path == '/server/gcode_store':
                self._handle_gcode_store()
            else:
                # Return 404 for unknown endpoints
                self._send_json_response({'error': f'Endpoint not found: {path}'}, 404)
                
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
            
            # Route requests
            if path == '/api/printer/gcode/script':
                self._handle_gcode_script(data)
            elif path == '/api/printer/emergency_stop':
                self._handle_emergency_stop()
            elif path == '/api/printer/restart':
                self._handle_printer_restart()
            else:
                self._send_json_response({'error': f'POST endpoint not found: {path}'}, 404)
                
        except Exception as e:
            logger.error(f"Error handling POST {self.path}: {e}")
            self._send_json_response({'error': 'Internal server error'}, 500)
    
    def _handle_printer_info(self):
        """Handle /api/printer/info request"""
        info = {
            'state': 'ready',
            'state_message': 'Printer is ready',
            'hostname': 'mock-printer',
            'software_version': 'v0.12.0-mock',
            'cpu_info': 'Mock CPU',
            'python_version': '3.9.0',
            'log_file': '/tmp/klippy.log'
        }
        self._send_json_response({'result': info})
    
    def _handle_printer_objects_query(self):
        """Handle /api/printer/objects/query request"""
        # Load mock printer status
        status_data = self._load_mock_data('printer_status.json')
        
        # Return data in Moonraker format
        response = {
            'result': {
                'status': status_data,
                'eventtime': time.time()
            }
        }
        
        self._send_json_response(response)
    
    def _handle_server_info(self):
        """Handle /server/info request"""
        info = {
            'klippy_connected': True,
            'klippy_state': 'ready',
            'components': ['file_manager', 'klippy_apis', 'machine', 'data_store'],
            'failed_components': [],
            'registered_directories': ['config', 'logs', 'gcodes'],
            'warnings': [],
            'websocket_count': 0,
            'moonraker_version': 'v0.8.0-mock',
            'missing_klippy_requirements': [],
            'api_version': [1, 0, 0],
            'api_version_string': '1.0.0'
        }
        self._send_json_response({'result': info})
    
    def _handle_server_config(self):
        """Handle /server/config request"""
        config = {
            'config': {
                'server': {
                    'host': '0.0.0.0',
                    'port': 7125,
                    'klippy_uds_address': '/tmp/klippy_uds',
                    'max_upload_size': 1024
                },
                'file_manager': {
                    'config_path': '~/printer_data/config',
                    'log_path': '~/printer_data/logs',
                    'queue_gcode_uploads': False
                },
                'machine': {
                    'provider': 'systemd_dbus'
                }
            }
        }
        self._send_json_response({'result': config})
    
    def _handle_files_list(self):
        """Handle /server/files/list request"""
        files = {
            'gcodes': [],
            'config': [
                {
                    'path': 'printer.cfg',
                    'modified': time.time(),
                    'size': 2048,
                    'permissions': 'rw'
                }
            ],
            'logs': []
        }
        self._send_json_response({'result': files})
    
    def _handle_gcode_store(self):
        """Handle /server/gcode_store request"""
        # Return recent G-code commands
        gcode_store = {
            'gcode_store': [
                {
                    'message': 'Printer is ready',
                    'time': time.time() - 10,
                    'type': 'response'
                },
                {
                    'message': 'ok T:22.5 /0.0 B:21.8 /0.0',
                    'time': time.time() - 5,
                    'type': 'response'
                }
            ]
        }
        self._send_json_response({'result': gcode_store})
    
    def _handle_gcode_script(self, data):
        """Handle G-code script execution"""
        script = data.get('script', '')
        
        logger.info(f"Mock G-code execution: {script}")
        
        # Simulate command execution
        response = {
            'result': 'ok'
        }
        
        self._send_json_response(response)
    
    def _handle_emergency_stop(self):
        """Handle emergency stop request"""
        logger.warning("Mock emergency stop triggered")
        
        response = {
            'result': 'Emergency stop executed'
        }
        
        self._send_json_response(response)
    
    def _handle_printer_restart(self):
        """Handle printer restart request"""
        logger.info("Mock printer restart triggered")
        
        response = {
            'result': 'Printer restart initiated'
        }
        
        self._send_json_response(response)
    
    def _load_mock_data(self, filename):
        """Load mock data from JSON file"""
        file_path = self.mock_data_dir / filename
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Mock data file not found: {filename}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filename}: {e}")
            return {}
    
    def _send_json_response(self, data, status_code=200):
        """Send JSON response"""
        json_data = json.dumps(data, indent=2)
        
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Length', str(len(json_data)))
        self.end_headers()
        self.wfile.write(json_data.encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.debug(f"HTTP: {format % args}")

def main():
    """Start the mock Moonraker server"""
    host = 'localhost'
    port = 7125
    
    print(f"🚀 Mock Moonraker Server starting...")
    print(f"📡 Server running at: http://{host}:{port}")
    print(f"🔧 Moonraker API Base: http://{host}:{port}/api")
    print(f"💡 Use Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        server = HTTPServer((host, port), MockMoonrakerHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n🛑 Server stopped by user")
        server.server_close()
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use. Please stop any existing Moonraker or mock servers.")
        else:
            print(f"❌ Server error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == '__main__':
    main()