#!/usr/bin/env python3
"""
Printer Buddy Development Startup Script

This script starts Printer Buddy in DEVELOPMENT MODE:
- Always uses MOCK hardware (no real printer required)
- Perfect for UI development and testing
- Safe to run without any printer hardware connected

Usage:
    python start_development.py
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add the printer_buddy directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.utils.manager import PrinterBuddyCore

async def main():
    """Main startup function for development mode"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("🔧 Starting Printer Buddy in DEVELOPMENT MODE...")
    logger.info("📋 Hardware: MOCK (no real printer required)")
    logger.info("🎯 Perfect for UI development and testing")
    
    try:
        # Create core manager in MOCK mode
        core = PrinterBuddyCore(hardware_mode="mock")
        
        # Initialize the system
        success = await core.initialize_all_modules()
        
        if not success:
            logger.error("❌ Failed to initialize Printer Buddy")
            return 1
            
        logger.info("✅ Printer Buddy initialized successfully")
        
        # Start API server
        logger.info("🚀 Starting API server on http://localhost:8080")
        core.start_api_server()
        
        logger.info("=" * 50)
        logger.info("🔧 DEVELOPMENT MODE ACTIVE")
        logger.info("📱 Web interface: http://localhost:8080")
        logger.info("🎯 All printer operations are SIMULATED")
        logger.info("⚡ Safe for UI development without hardware")
        logger.info("🛑 Press Ctrl+C to stop")
        logger.info("=" * 50)
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down development server...")
        if 'core' in locals():
            await core.shutdown()
        return 0
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Development server stopped by user")
        sys.exit(0)