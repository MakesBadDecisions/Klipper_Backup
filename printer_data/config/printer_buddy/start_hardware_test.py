#!/usr/bin/env python3
"""
Printer Buddy Hardware Test Startup Script

This script starts Printer Buddy in HARDWARE TEST MODE:
- Always uses REAL hardware (requires Moonraker connection)
- Connects to actual printer via Moonraker API
- Will FAIL if no printer hardware is available
- Use this for testing with real printer hardware

Usage:
    python start_hardware_test.py
    python start_hardware_test.py --moonraker-url http://192.168.1.100:7125
"""

import sys
import asyncio
import logging
import argparse
from pathlib import Path

# Add the printer_buddy directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.utils.manager import PrinterBuddyCore

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Printer Buddy Hardware Test Mode')
    parser.add_argument('--moonraker-url', default='http://localhost:7125',
                       help='Moonraker API URL (default: http://localhost:7125)')
    return parser.parse_args()

async def main():
    """Main startup function for hardware test mode"""
    args = parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("🔧 Starting Printer Buddy in HARDWARE TEST MODE...")
    logger.info(f"🖨️  Hardware: REAL (Moonraker: {args.moonraker_url})")
    logger.info("⚠️  Requires actual printer hardware to function")
    
    try:
        # Create core manager in REAL hardware mode
        core = PrinterBuddyCore(hardware_mode="real", moonraker_url=args.moonraker_url)
        
        # TODO: Add hardware connectivity check here
        logger.info(f"🔍 Checking connection to Moonraker at {args.moonraker_url}...")
        # This will be implemented when we add real Moonraker communication
        
        # Initialize the system
        success = await core.initialize_all_modules()
        
        if not success:
            logger.error("❌ Failed to initialize Printer Buddy")
            logger.error("💡 Try start_development.py for mock hardware testing")
            return 1
            
        logger.info("✅ Printer Buddy initialized successfully")
        
        # Start API server
        logger.info("🚀 Starting API server on http://localhost:8080")
        core.start_api_server()
        
        logger.info("=" * 60)
        logger.info("🖨️  HARDWARE TEST MODE ACTIVE")
        logger.info("📱 Web interface: http://localhost:8080")
        logger.info(f"🔗 Connected to Moonraker: {args.moonraker_url}")
        logger.info("⚡ All printer operations are REAL")
        logger.info("⚠️  BE CAREFUL - this controls actual hardware!")
        logger.info("🛑 Press Ctrl+C to stop")
        logger.info("=" * 60)
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down hardware test server...")
        if 'core' in locals():
            await core.shutdown()
        return 0
    except Exception as e:
        logger.error(f"❌ Hardware test failed: {e}")
        logger.error("💡 Check printer connection and try start_development.py for mock testing")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Hardware test server stopped by user")
        sys.exit(0)