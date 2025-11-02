#!/usr/bin/env python3
"""
WebSocket handler for Mock Moonraker Server
Simulates Moonraker WebSocket messages for testing
"""

import asyncio
import json
import time
import websockets
import threading
from websockets.server import serve

class MockMoonrakerWebSocket:
    def __init__(self, port=7126):
        self.port = port
        self.clients = set()
        self.running = False
        
    async def register(self, websocket, path):
        """Register a new WebSocket client"""
        self.clients.add(websocket)
        print(f"Client connected. Total clients: {len(self.clients)}")
        
        # Send initial connection acknowledgment
        initial_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "websocket_id": 12345,
                "klippy_connected": True,
                "klippy_state": "ready"
            }
        }
        await websocket.send(json.dumps(initial_response))
        
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)
            print(f"Client disconnected. Total clients: {len(self.clients)}")
    
    async def broadcast_message(self, message):
        """Broadcast a message to all connected clients"""
        if self.clients:
            # Remove disconnected clients
            disconnected = set()
            for client in self.clients:
                try:
                    await client.send(json.dumps(message))
                except websockets.exceptions.ConnectionClosed:
                    disconnected.add(client)
            
            # Clean up disconnected clients
            self.clients -= disconnected
    
    async def simulate_console_messages(self):
        """Simulate periodic console messages"""
        console_messages = [
            "ok",
            "// Temperature readings: B:21.8°C T0:22.5°C",
            "// Position: X:135.0 Y:135.0 Z:5.0 E:0.0",
            "// Printer is ready",
            "ok T:22.5 /0.0 B:21.8 /0.0",
            "// Homing complete",
            "!! Error: Cold extrusion prevented",
            "// Fan speed: 0%"
        ]
        
        while self.running:
            await asyncio.sleep(5)  # Send a message every 5 seconds
            
            if self.clients:
                message_text = console_messages[int(time.time()) % len(console_messages)]
                message = {
                    "jsonrpc": "2.0",
                    "method": "notify_gcode_response",
                    "params": [message_text]
                }
                await self.broadcast_message(message)
    
    async def simulate_status_updates(self):
        """Simulate periodic status updates"""
        while self.running:
            await asyncio.sleep(10)  # Send status update every 10 seconds
            
            if self.clients:
                # Simulate temperature fluctuation
                base_temp = 22.0
                variation = (time.time() % 60) / 60 * 2 - 1  # -1 to +1
                
                status_message = {
                    "jsonrpc": "2.0",
                    "method": "notify_status_update",
                    "params": [
                        {
                            "extruder": {
                                "temperature": base_temp + variation,
                                "target": 0.0
                            },
                            "heater_bed": {
                                "temperature": base_temp - 0.2 + variation * 0.5,
                                "target": 0.0
                            }
                        },
                        time.time()
                    ]
                }
                await self.broadcast_message(status_message)
    
    async def start_server(self):
        """Start the WebSocket server"""
        self.running = True
        
        print(f"🔌 Mock WebSocket server starting on port {self.port}...")
        
        # Start background tasks
        asyncio.create_task(self.simulate_console_messages())
        asyncio.create_task(self.simulate_status_updates())
        
        # Start WebSocket server
        async with serve(self.register, "localhost", self.port):
            print(f"🔌 WebSocket server running at ws://localhost:{self.port}")
            while self.running:
                await asyncio.sleep(1)
    
    def stop(self):
        """Stop the WebSocket server"""
        self.running = False

def start_websocket_server(port=7126):
    """Start WebSocket server in a new event loop"""
    def run_server():
        asyncio.new_event_loop().run_until_complete(
            MockMoonrakerWebSocket(port).start_server()
        )
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    return thread

if __name__ == '__main__':
    asyncio.run(MockMoonrakerWebSocket().start_server())