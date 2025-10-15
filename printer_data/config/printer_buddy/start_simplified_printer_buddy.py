#!/usr/bin/env python3
"""
Simplified Printer Buddy Core

This simplified version focuses only on the commissioning test framework.
The web UI now communicates directly with Moonraker API.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the printer_buddy directory to Python path
PRINTER_BUDDY_DIR = Path(__file__).parent
sys.path.insert(0, str(PRINTER_BUDDY_DIR))

from core.utils.state_manager import StateManager
from core.utils.event_bus import EventBus
from core.modules.printer_tests_module import PrinterTestsModule


# Configure logging to be clean and focused
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)


class SimplifiedPrinterBuddy:
    """
    Simplified Printer Buddy Core
    
    Only handles the commissioning test framework.
    All printer communication happens directly from the web UI to Moonraker.
    """
    
    def __init__(self):
        self.logger = logging.getLogger('PrinterBuddy')
        self.state_manager = StateManager()
        self.event_bus = EventBus()
        self.test_module = None
        self.running = False
        
    async def initialize(self):
        """Initialize the simplified system"""
        try:
            self.logger.info("Initializing Simplified Printer Buddy")
            
            # Initialize core components
            await self.state_manager.initialize()
            await self.event_bus.initialize()
            
            # Initialize test module
            self.test_module = PrinterTestsModule(
                state_manager=self.state_manager,
                event_bus=self.event_bus
            )
            await self.test_module.initialize()
            
            # Set initial state
            self.state_manager.set('system.mode', 'simplified')
            self.state_manager.set('system.version', '2.0-simplified')
            self.state_manager.set('system.status', 'ready')
            
            self.logger.info("Simplified Printer Buddy initialized successfully")
            self.running = True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            raise
            
    async def run(self):
        """Main run loop - just keeps the test framework alive"""
        self.logger.info("Simplified Printer Buddy is running")
        self.logger.info("Web UI should connect directly to Moonraker on port 7125")
        self.logger.info("Test framework is available for commissioning tests")
        
        try:
            while self.running:
                # Just sleep and let the test framework handle its own lifecycle
                await asyncio.sleep(10)
                
                # Periodic health check
                if self.running:
                    self.logger.debug("System running normally")
                    
        except KeyboardInterrupt:
            self.logger.info("Shutdown requested by user")
        except Exception as e:
            self.logger.error(f"Runtime error: {e}")
        finally:
            await self.shutdown()
            
    async def shutdown(self):
        """Clean shutdown"""
        try:
            self.running = False
            self.logger.info("Shutting down Simplified Printer Buddy")
            
            if self.test_module:
                await self.test_module.shutdown()
                
            if self.event_bus:
                await self.event_bus.shutdown()
                
            if self.state_manager:
                await self.state_manager.shutdown()
                
            self.logger.info("Shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


def main():
    """Main entry point"""
    print("=" * 60)
    print("Simplified Printer Buddy v2.0")
    print("Direct Moonraker Integration")
    print("=" * 60)
    print()
    print("ARCHITECTURE CHANGE:")
    print("- Web UI connects directly to Moonraker API (port 7125)")
    print("- Python backend provides only test framework")
    print("- No more API proxy - much simpler and more reliable!")
    print()
    print("TO USE:")
    print("1. Ensure Moonraker is running on port 7125")
    print("2. Open web UI and connect to Moonraker directly")
    print("3. Use commissioning tests as needed")
    print()
    
    # Create and run the simplified system
    buddy = SimplifiedPrinterBuddy()
    
    try:
        asyncio.run(buddy.initialize())
        asyncio.run(buddy.run())
    except KeyboardInterrupt:
        print("\nShutdown requested")
    except Exception as e:
        print(f"Error: {e}")
        return 1
        
    return 0


if __name__ == '__main__':
    sys.exit(main())