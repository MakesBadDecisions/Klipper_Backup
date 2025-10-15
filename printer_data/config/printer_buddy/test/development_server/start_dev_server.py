#!/usr/bin/env python3
"""
Development Server Startup Script
Starts the mock Moonraker API server for local development
"""

import os
import sys
import subprocess
import time

def main():
    """Start the development server"""
    print("🔧 Printer Buddy Development Server")
    print("=" * 50)
    
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    mock_server_path = os.path.join(current_dir, 'mock_moonraker_simple.py')
    
    # Check if mock server exists
    if not os.path.exists(mock_server_path):
        print(f"❌ Error: Mock server not found at {mock_server_path}")
        return 1
    
    print("🚀 Starting Mock Moonraker API Server...")
    print("📍 This simulates Moonraker API for local UI development")
    print("🌐 Access your Printer Buddy UI and it will connect to mock data")
    print("")
    
    try:
        # Start the mock server
        subprocess.run([sys.executable, mock_server_path], check=True)
    except KeyboardInterrupt:
        print("\n👋 Development server stopped")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting server: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())