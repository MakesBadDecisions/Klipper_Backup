# Printer Buddy Test Module

This module contains all testing, development, and reference materials for Printer Buddy development. It provides a complete local development environment that mimics the real Moonraker API for UI development and testing.

## Directory Structure

```
test/
├── README.md                    # This file - overview and usage guide
├── moonraker_api_reference/     # Moonraker API documentation and examples
│   ├── README.md               # API reference documentation
│   ├── printer_objects.json   # Real Moonraker printer object examples
│   ├── websocket_messages.json # WebSocket message examples
│   └── api_endpoints.json     # REST API endpoint documentation
├── mock_data/                  # Mock printer data for testing
│   ├── README.md              # Mock data documentation
│   ├── printer_status.json    # Mock printer status responses
│   ├── temperature_data.json  # Mock temperature readings
│   ├── print_jobs.json        # Mock print job data
│   └── configuration.json     # Mock printer configuration
├── development_server/         # Local development server
│   ├── README.md              # Server setup and usage
│   ├── mock_moonraker.py      # Local Moonraker API simulator
│   ├── websocket_server.py    # WebSocket message simulator
│   └── start_dev_server.py    # Development server startup script
└── integration_tests/          # Integration test scripts
    ├── README.md              # Test documentation
    ├── test_api_endpoints.py   # API endpoint tests
    ├── test_websocket.py       # WebSocket communication tests
    └── test_ui_integration.py  # UI integration tests
```

## Quick Start

### 1. Start Development Server
```bash
cd test/development_server
python start_dev_server.py
```

### 2. Access Local UI
- Open browser to `http://localhost:8080`
- UI will connect to mock Moonraker API instead of real printer
- All printer data is simulated but realistic

### 3. Modify Mock Data
- Edit files in `mock_data/` to test different printer states
- Server automatically reloads mock data without restart
- Test error conditions, temperature changes, print jobs, etc.

## Development Workflow

1. **UI Development**: Use mock server for rapid UI iteration without printer hardware
2. **API Testing**: Validate API calls against realistic Moonraker responses
3. **Integration Testing**: Test complete workflows with mock data
4. **Documentation**: Reference real Moonraker API examples for accuracy

## Key Features

- **Realistic Mock Data**: Based on real Moonraker API responses from actual printers
- **WebSocket Simulation**: Mock real-time printer updates (temperature, position, status)
- **API Endpoint Coverage**: Complete REST API simulation for all Printer Buddy features
- **Hot Reload**: Mock data changes are reflected immediately without server restart
- **Error Simulation**: Test error conditions and edge cases safely

## Integration with Main System

- Mock data structure matches production Moonraker API exactly
- Same API calls work in both development and production environments
- UI code requires no changes when switching between mock and real API
- Configuration files can be tested with mock printer configs

## Best Practices

1. **Keep Mock Data Realistic**: Base all mock responses on real Moonraker data
2. **Test Edge Cases**: Use mock data to test error conditions safely
3. **Document Changes**: Update API reference when Moonraker API changes
4. **Version Control**: Track mock data changes to understand test evolution
5. **Performance Testing**: Use mock server to test UI performance with large datasets

## References

- [Moonraker API Documentation](https://moonraker.readthedocs.io/en/latest/web_api/)
- [Klipper Configuration Reference](https://www.klipper3d.org/Config_Reference.html)
- [WebSocket API Reference](https://moonraker.readthedocs.io/en/latest/web_api/#websocket-api-overview)

---

**Note**: This test module is designed to accelerate development while maintaining production accuracy. All mock data should reflect real-world printer behavior and API responses.