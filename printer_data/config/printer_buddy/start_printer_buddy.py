#!/usr/bin/env python3
"""
Printer Buddy Production Startup Script

This script starts Printer Buddy in PRODUCTION MODE:
- Smart auto-detection: tries real hardware, falls back to mock
- Automatic connection to Moonraker if available
- Safe fallback to mock mode for development
- Best choice for normal usage

Usage:
    python start_printer_buddy.py                    # Auto-detect hardware
    python start_printer_buddy.py --hardware mock    # Force mock mode  
    python start_printer_buddy.py --hardware real    # Force real hardware
    python start_printer_buddy.py --moonraker-url http://192.168.1.100:7125
"""

import sys
import asyncio
import logging
import argparse
from pathlib import Path

# Add the printer_buddy directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.utils.manager import PrinterBuddyCore

# ============================================================================
# HARDWARE MODE CONFIGURATION - Simple hardcoded control
# ============================================================================
# Uncomment ONE of these lines to set the hardware mode:

#USE_MOCK_HARDWARE = True          # Mock mode - safe development/testing
USE_REAL_HARDWARE = True            # Real mode - connects to actual printer

# Moonraker URL (only used in real hardware mode)
MOONRAKER_URL = "http://localhost:7125"

# ============================================================================

async def main():
    """Main startup function with hardcoded hardware selection"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Printer Buddy (Production Mode)...")
    
    # Determine hardware mode from hardcoded defines
    if 'USE_REAL_HARDWARE' in globals() and USE_REAL_HARDWARE:
        hardware_mode = "real"
        moonraker_url = MOONRAKER_URL
        logger.info("HARDCODED: Using REAL hardware mode")
        logger.info(f"Moonraker URL: {moonraker_url}")
    else:
        hardware_mode = "mock"
        moonraker_url = "http://localhost:7125"  # Unused in mock mode
        logger.info("HARDCODED: Using MOCK hardware mode")
    
    try:
        # Create core manager with hardcoded hardware mode
        core = PrinterBuddyCore(hardware_mode=hardware_mode, moonraker_url=moonraker_url)
        
        # Initialize the system
        success = await core.initialize_all_modules()
        
        if not success:
            logger.error("❌ Failed to initialize Printer Buddy")
            return 1
            
        logger.info("Printer Buddy initialized successfully")
        
        # Start API server
        logger.info("Starting API server on http://localhost:8080")
        core.start_api_server()
        
        # Display status based on actual connection status
        logger.info("=" * 60)
        if hardware_mode == "real":
            if getattr(core, 'connection_status', 'unknown') == "connected":
                logger.info("PRODUCTION MODE - REAL HARDWARE")
                logger.info("Web interface: http://localhost:8080")
                logger.info(f"Connected to Moonraker: {moonraker_url}")
                logger.info("All printer operations are REAL")
                logger.info("BE CAREFUL - this controls actual hardware!")
            else:
                logger.info("REAL HARDWARE MODE - CONNECTION FAILED")
                logger.info("Web interface: http://localhost:8080")
                logger.info(f"Cannot connect to Moonraker: {moonraker_url}")
                logger.info("Printer operations will FAIL until connection restored")
                logger.info("Check printer power, Moonraker service, network")
        else:
            logger.info("PRODUCTION MODE - MOCK HARDWARE")
            logger.info("Web interface: http://localhost:8080")
            logger.info("All printer operations are SIMULATED")
            logger.info("To use real hardware, edit start_printer_buddy.py")
            
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        
        # Keep running
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutdown requested...")
            
        # Cleanup
        await core.shutdown()
        logger.info("Printer Buddy stopped")
        return 0
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))