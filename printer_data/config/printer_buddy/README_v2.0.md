# Printer Buddy v2.0 - Simplified Architecture

## Overview

This is a major architectural simplification of Printer Buddy. Instead of running our own API proxy server, the web UI now communicates directly with Moonraker API.

## Architecture Changes

### Before (v1.x)
```
Web UI → Printer Buddy API Server → Moonraker → Klipper
                ↓
            Complex HTTP server
            Async event loops  
            Connection management
            API proxy layer
```

### After (v2.0)
```
Web UI → Moonraker → Klipper
           ↓
    Python Test Framework (Optional)
```

## Benefits

1. **Reliability**: No proxy layer to fail or get out of sync
2. **Simplicity**: Much less code, fewer moving parts
3. **Standards Compliance**: Direct Moonraker API usage like other Klipper UIs
4. **Performance**: Direct communication, no extra network hops
5. **Maintainability**: Less code to debug and maintain

## What Still Works

- ✅ Real-time printer status display
- ✅ Temperature control (bed/extruder)
- ✅ G-code console commands
- ✅ Movement controls (jog/home)
- ✅ Emergency stop
- ✅ Commissioning test framework (optional)

## What Changed

- ❌ No more Printer Buddy API server on port 8080
- ❌ No more API proxy layer
- ❌ No more complex async connection management
- ✅ Web UI connects directly to Moonraker on port 7125
- ✅ Python backend is optional and only runs test framework

## Usage

### Option 1: Web UI Only (Simplest)
1. Ensure Moonraker is running on port 7125
2. Open `web/index.html` in a browser
3. Everything works directly with Moonraker

### Option 2: With Test Framework
1. Run: `python start_simplified_printer_buddy.py`
2. Open `web/index.html` in a browser
3. Commissioning tests are available if needed

## File Changes

### New Files
- `start_simplified_printer_buddy.py` - Simplified Python backend
- `web/js/core/moonraker-api.js` - Direct Moonraker API client

### Modified Files
- `web/js/app.js` - Uses Moonraker API directly
- `web/js/panels/console.js` - Direct G-code to Moonraker
- `web/js/panels/temperature.js` - Direct temperature control
- `web/js/panels/controls.js` - Direct movement commands

### Deprecated Files
- `api/server.py` - No longer needed
- `start_printer_buddy.py` - Replaced by simplified version

## API Endpoints Used

All communication now uses standard Moonraker API endpoints:

- `GET /printer/info` - Printer information
- `GET /printer/objects/query` - Real-time status
- `POST /printer/gcode/script` - Execute G-code
- WebSocket `/websocket` - Real-time updates (future)

## Migration Guide

If you were using the old version:

1. Stop the old `start_printer_buddy.py`
2. Optionally run `start_simplified_printer_buddy.py` for tests
3. Open the web UI - it now works directly with Moonraker
4. Remove old API proxy dependencies

## Development

The system is now much easier to develop:

1. **Frontend**: Pure HTML/JS talking to Moonraker
2. **Backend**: Optional Python for test framework only
3. **Testing**: Use Moonraker's mock/test modes
4. **Debugging**: Standard Moonraker API tools

This represents a significant simplification while maintaining all core functionality!