# Development Server Documentation

This directory contains the local development server that simulates Moonraker API for UI development and testing without requiring a real 3D printer.

## File Overview

### `start_dev_server.py`
Main entry point for the development server. Starts both HTTP REST API server and WebSocket server on different ports to simulate real Moonraker behavior.

### `mock_moonraker.py`
HTTP server that implements Moonraker REST API endpoints using mock data. Provides realistic responses for all API calls that Printer Buddy uses.

### `websocket_server.py`
WebSocket server that simulates real-time printer status updates. Sends periodic status updates, temperature changes, and print progress notifications.

## Quick Start

### 1. Start the Development Server
```bash
cd test/development_server
python start_dev_server.py
```

### 2. Server Endpoints
- **REST API**: `http://localhost:7125` (matches real Moonraker port)
- **WebSocket**: `ws://localhost:7125/websocket`
- **Web UI**: Access via Printer Buddy's web interface

### 3. Configuration
The server automatically loads mock data from `../mock_data/` directory and serves it through realistic API endpoints.

## Features

### REST API Simulation
- **Complete API Coverage**: All Moonraker endpoints used by Printer Buddy
- **Realistic Responses**: Based on actual Moonraker API responses
- **Error Simulation**: Test error conditions and edge cases
- **Dynamic Data**: Mock data changes over time to simulate printer behavior

### WebSocket Simulation
- **Real-time Updates**: Periodic status updates matching real printer behavior
- **State Changes**: Simulates heating, printing, pausing, and completion
- **Error Events**: Emergency stops, disconnections, and hardware failures
- **Subscription Model**: Matches Moonraker's object subscription system

### Mock Data Integration
- **Hot Reload**: Changes to mock data files are reflected immediately
- **State Consistency**: Related objects maintain consistent states
- **Realistic Timing**: Temperature changes, print progress follow real patterns
- **Multiple Scenarios**: Switch between different printer states for testing

## API Endpoints Implemented

### Core Endpoints
- `GET /server/info` - Server information
- `GET /printer/info` - Printer status
- `POST /printer/emergency_stop` - Emergency stop
- `GET /printer/objects/query` - Query printer objects
- `POST /printer/gcode/script` - Execute G-code

### Print Job Control
- `POST /printer/print/start` - Start print job
- `POST /printer/print/pause` - Pause print job
- `POST /printer/print/resume` - Resume print job
- `POST /printer/print/cancel` - Cancel print job

### File Management
- `GET /server/files/list` - List files
- `GET /server/files/metadata` - File metadata
- `GET /server/temperature_store` - Temperature history

## WebSocket Messages

### Status Updates
- Temperature changes (extruder, bed)
- Print progress updates
- Position changes
- Fan speed changes

### State Transitions
- Print start/pause/resume/cancel
- Heating/cooling cycles
- Homing operations
- Error conditions

### Client Subscriptions
- Object subscription requests
- Real-time status notifications
- G-code response messages
- File system notifications

## Development Workflow

### 1. UI Development
- Start dev server
- Access Printer Buddy UI
- UI connects to mock API automatically
- Test all features without real printer

### 2. API Testing
- Test new API calls against mock server
- Validate request/response formats
- Test error handling

### 3. State Testing
- Modify mock data to test different states
- Test UI responses to various conditions
- Validate error recovery

### 4. Performance Testing
- Test UI with large datasets
- Validate WebSocket message handling
- Test concurrent connections

## Configuration Options

### Server Settings
- **Port**: Default 7125 (matches Moonraker)
- **Host**: localhost (development only)
- **CORS**: Enabled for local development
- **Logging**: Configurable debug levels

### Mock Data Settings
- **Auto-reload**: Enabled by default
- **State progression**: Configurable timing
- **Error injection**: Manual or automatic
- **Data validation**: Against real API schemas

## Extending the Server

### Adding New Endpoints
1. Add endpoint handler to `mock_moonraker.py`
2. Create corresponding mock data
3. Update API documentation
4. Test with UI integration

### Adding WebSocket Events
1. Add event type to `websocket_server.py`
2. Create mock event data
3. Update subscription handling
4. Test real-time behavior

### Custom Mock Scenarios
1. Create new mock data files
2. Add scenario switching logic
3. Update UI to test scenarios
4. Document new test cases

## Troubleshooting

### Server Won't Start
- Check port 7125 is not in use
- Verify Python dependencies installed
- Check mock data file syntax

### WebSocket Connection Issues
- Verify WebSocket endpoint URL
- Check browser developer console
- Validate subscription messages

### Mock Data Issues
- Validate JSON syntax
- Check data consistency
- Verify against API schemas

---

This development server enables rapid UI development and testing while maintaining complete compatibility with the real Moonraker API used in production.