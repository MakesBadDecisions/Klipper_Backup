# Mock Data Documentation

This directory contains realistic mock data for testing Printer Buddy UI and functionality. All mock data is based on real Moonraker API responses to ensure accuracy.

## File Overview

### `printer_status.json`
Complete printer status data that matches real Moonraker responses. Includes all objects that Printer Buddy uses:
- Print statistics and current state
- Temperature readings for extruder and bed
- Toolhead position and movement data
- Fan speeds and other hardware status

### `temperature_data.json`
Historical temperature data for creating realistic temperature graphs and trends. Includes:
- Multiple temperature readings over time
- Heating curves from cold start to target
- Stable temperature maintenance data
- Cool-down sequences

### `print_jobs.json`
Various print job scenarios for testing different UI states:
- Print job starting and initialization
- Active printing with progress updates
- Paused print scenarios
- Completed print jobs
- Failed/cancelled print jobs

### `configuration.json`
Mock printer configuration data that simulates what would be parsed from printer.cfg:
- Axis limits and kinematics
- Temperature limits and safety settings
- Stepper motor configurations
- Sensor configurations

## Data Scenarios

### Cold Printer (Standby)
- All temperatures at ambient
- No active print job
- Printer homed and ready
- All systems normal

### Heating Phase
- Temperatures ramping up to targets
- Extruder and bed heating curves
- Power levels changing as temperatures approach targets
- Status messages reflecting heating progress

### Active Printing
- Print job in progress with realistic timing
- Temperature stability during print
- Toolhead position updates
- Layer progress and completion estimates
- Fan speeds responding to print requirements

### Print Completion
- Final print statistics
- Temperature cool-down sequences
- Final toolhead positioning
- Success/failure status messages

### Error Conditions
- Temperature runaway scenarios
- Printer disconnection states
- Emergency stop conditions
- Hardware fault simulations

## Usage Guidelines

1. **State Consistency**: Related data points must be consistent (e.g., if printing, temperatures should be at target)
2. **Realistic Timing**: Use realistic durations for heating, printing, and cooling
3. **Progressive Updates**: Show gradual changes, not instant state transitions
4. **Error Handling**: Include realistic error messages and recovery procedures
5. **Hardware Limits**: Respect real printer physical and safety limits

## Integration with Development Server

The development server uses this mock data to:
- Respond to API queries with realistic data
- Send WebSocket updates that match real printer behavior
- Simulate state transitions over time
- Test error conditions safely

## Updating Mock Data

When updating mock data:
1. Base changes on real Moonraker API responses
2. Maintain data consistency across related objects
3. Update documentation if new scenarios are added
4. Test UI responses to data changes
5. Validate against current Moonraker API version

---

All mock data represents realistic 3D printer behavior and should closely match what would be seen from a real QIDI X-Max 3 printer running Klipper and Moonraker.