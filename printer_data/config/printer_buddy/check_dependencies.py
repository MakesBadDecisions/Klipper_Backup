#!/usr/bin/env python3
"""
Dependency Check Script for Printer Buddy

Run this script on the Raspberry Pi to verify all dependencies are available.
"""

import sys
import subprocess

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7+ required")
        return False
    
    print("✅ Python version OK")
    return True

def check_module(module_name, description=""):
    """Check if a Python module is available"""
    try:
        __import__(module_name)
        print(f"✅ {module_name} - available {description}")
        return True
    except ImportError:
        print(f"❌ {module_name} - MISSING {description}")
        return False

def check_moonraker_connection():
    """Check if Moonraker is accessible"""
    try:
        import urllib.request
        import urllib.error
        import json
        
        with urllib.request.urlopen("http://localhost:7125/server/info", timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read())
                print(f"✅ Moonraker - accessible (klippy_connected: {data.get('klippy_connected', 'unknown')})")
                return True
    except Exception as e:
        print(f"❌ Moonraker - not accessible: {e}")
        return False

def main():
    """Run all dependency checks"""
    print("🔍 Printer Buddy Dependency Check")
    print("=" * 40)
    
    all_ok = True
    
    # Check Python version
    all_ok &= check_python_version()
    print()
    
    # Check required modules
    print("📦 Checking Python modules:")
    all_ok &= check_module("asyncio", "(async support)")
    all_ok &= check_module("configparser", "(config file parsing)")
    all_ok &= check_module("pathlib", "(path handling)")
    all_ok &= check_module("json", "(JSON processing)")
    all_ok &= check_module("logging", "(logging support)")
    all_ok &= check_module("http.server", "(HTTP server)")
    
    # Check optional but important modules
    print("\n🌐 Checking network modules:")
    aiohttp_ok = check_module("aiohttp", "(HTTP client for Moonraker)")
    if not aiohttp_ok:
        print("   Install with: pip3 install aiohttp")
        print("   Or: ~/klippy-env/bin/pip install aiohttp")
    all_ok &= aiohttp_ok
    
    # Check Moonraker connection
    print("\n🖨️  Checking printer connection:")
    moonraker_ok = check_moonraker_connection()
    if not moonraker_ok:
        print("   Make sure Klipper and Moonraker are running")
        print("   Check: systemctl status moonraker")
    
    print("\n" + "=" * 40)
    if all_ok and moonraker_ok:
        print("🎉 All checks passed! Ready for real hardware testing.")
        print("   Run: python3 start_printer_buddy.py")
    elif all_ok:
        print("⚠️  Dependencies OK, but Moonraker not available.")
        print("   Run: python3 start_development.py (mock mode)")
    else:
        print("❌ Missing dependencies. Install required modules first.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())