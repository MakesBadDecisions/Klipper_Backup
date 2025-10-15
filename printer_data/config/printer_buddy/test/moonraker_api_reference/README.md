# Moonraker API Reference

This directory contains comprehensive reference documentation for the Moonraker API, based on real API responses and official documentation. Use these references when building mock data and implementing UI features.

## File Overview

### `printer_objects.json`
Real Moonraker printer object data structure with all available objects and their properties. This is the foundation for understanding what data is available from a real printer.

### `websocket_messages.json`
Examples of all WebSocket message types that Moonraker sends, including:
- Status updates
- Temperature changes  
- Print progress
- Error notifications
- Configuration changes

### `api_endpoints.json`
Complete REST API endpoint documentation with:
- Request methods and URLs
- Required parameters
- Response formats
- Error conditions
- Example requests and responses

## Key Moonraker Objects for Printer Buddy

Based on our UI requirements, these are the most important objects:

### Core Status Objects
- `printer.print_stats` - Print job status, state, filename
- `printer.display_status` - Current message, progress percentage
- `printer.virtual_sdcard` - File position, progress

### Temperature Objects  
- `printer.extruder` - Hotend temperature, target, power
- `printer.heater_bed` - Bed temperature, target, power
- `printer.temperature_host` - Host system temperature

### Motion Objects
- `printer.toolhead` - Position, homed axes, max velocity
- `printer.gcode_move` - Absolute/relative coordinates, speed factor

### Safety Objects
- `printer.pause_resume` - Pause/resume state
- `printer.emergency_stop` - Emergency stop status
- `printer.firmware_retraction` - Retraction settings

## WebSocket Subscription Patterns

Printer Buddy subscribes to these object updates:

```javascript
// Essential subscriptions for core functionality
{
  "jsonrpc": "2.0",
  "method": "printer.objects.subscribe",
  "params": {
    "objects": {
      "print_stats": ["state", "filename", "print_duration"],
      "display_status": ["progress", "message"],
      "extruder": ["temperature", "target"],
      "heater_bed": ["temperature", "target"], 
      "toolhead": ["position", "homed_axes"],
      "pause_resume": ["is_paused"]
    }
  },
  "id": 1
}
```

## API Endpoint Usage

### Emergency Stop
```http
POST /printer/emergency_stop
```
Immediately halts all printer operations. No parameters required.

### Temperature Control
```http
POST /printer/gcode/script
Content-Type: application/json

{
  "script": "SET_EXTRUDER_TEMPERATURE TARGET=200"
}
```

### Print Job Control
```http
POST /printer/print/pause
POST /printer/print/resume  
POST /printer/print/cancel
```

## Mock Data Requirements

When creating mock data, ensure:

1. **Data Types Match**: Moonraker sends specific data types (float, int, string, bool)
2. **Object Structure**: Nested objects must match real Moonraker structure exactly
3. **State Consistency**: Related objects should have consistent states
4. **Realistic Values**: Temperature ranges, speeds, and positions should be realistic
5. **Error Conditions**: Include examples of error states and messages

## Testing Scenarios

Use these API references to test:

- **Cold Start**: Printer just powered on, not homed
- **Heating**: Extruder and bed reaching target temperatures
- **Printing**: Active print job with progress updates
- **Paused Print**: Print job paused mid-operation
- **Error States**: Various error conditions and recovery
- **Emergency Stop**: System shutdown and recovery

## Integration Notes

- All mock responses must validate against real Moonraker API
- WebSocket message timing should reflect real printer behavior
- API errors should match Moonraker error response format
- Object state changes should trigger appropriate WebSocket notifications

---

**Important**: This reference is based on Moonraker v0.8.0+. Always verify against the latest Moonraker documentation for production deployments.