# Printer Buddy Test System Documentation

## Overview
The Printer Buddy test system provides automated commissioning and validation tests for 3D printers. This document outlines each test, the test module architecture, and integration with the core manager.

## Test Architecture

### Three-Layer Integration
```
Core Manager (manager.py)
    ↓ event_bus & state_manager
PrinterTestsModule (printer_tests_module.py) 
    ↓ discovery & execution
Individual Tests (inherit from BaseTest)
    ↓ progress & status callbacks
Web UI via API Server (server.py)
```

### Test Discovery & Execution Flow
1. **PrinterTestsModule** dynamically discovers all test classes in `printer_tests/` directory
2. Tests inherit from **BaseTest** providing common lifecycle methods
3. **Core Manager** coordinates via EventBus and StateManager
4. **API Server** exposes test endpoints to web UI
5. Tests communicate back via callbacks (progress, status, user_prompt)

## Available Tests

### 1. Safety Validation Test (`safety_validation.py`)
- **Purpose**: Essential safety checks that must pass before any other tests
- **Category**: Safety
- **Duration**: 2-3 minutes
- **Dependencies**: None (runs first)
- **Description**: Tests communication with printer, verifies e-stop functionality (honor system), validates basic printer.cfg parameters
- **Special Features**: Includes user interaction for emergency stop verification

### 2. Basic Movement Test (`basic_movement_test.py`)
- **Purpose**: Test basic X/Y/Z axis movement within safe limits
- **Category**: Motion
- **Duration**: 3-5 minutes
- **Dependencies**: safety_validation
- **Description**: Validates fundamental stepper motor movement, position feedback, and checks for mechanical binding or issues

### 3. Homing Test (`homing_test.py`)
- **Purpose**: Validate homing sequence for all configured axes
- **Category**: Motion
- **Duration**: 2-5 minutes (estimated)
- **Dependencies**: safety, basic movement
- **Description**: Tests individual axis homing, full G28 homing sequence, and verifies endstop triggering behavior

### 4. Endstops Test (`endstops_test.py`)
- **Purpose**: Test all configured endstops and limit switches
- **Category**: Safety/Motion
- **Duration**: 2-5 minutes (estimated)
- **Dependencies**: safety, homing
- **Description**: Interactive test guiding user through triggering each endstop, verifies state changes, tests endstop response during movement

### 5. Heating System Test (`heating_test.py`)
- **Purpose**: Validate bed and extruder heating systems
- **Category**: Heating
- **Duration**: 5-10 minutes
- **Dependencies**: safety_validation
- **Description**: Tests bed heater to safe temperature, extruder heating, temperature stability, and thermal runaway protection

### 6. Extruder Test (`extruder_test.py`)
- **Purpose**: Test extruder motor and filament handling systems
- **Category**: Extrusion
- **Duration**: 2-5 minutes (estimated)
- **Dependencies**: safety, heating
- **Description**: Tests extruder motor movement, extrusion at temperature, checks for clogs or binding, validates retraction functionality

### 7. Fans Test (`fans_test.py`)
- **Purpose**: Test all configured fans and cooling systems
- **Category**: Cooling
- **Duration**: 2-5 minutes (estimated)
- **Dependencies**: safety
- **Description**: Discovers and tests all configured fans (part cooling, hotend cooling, exhaust), tests at different speeds, checks RPM feedback if available

### 8. Kinematics Validation Test (`kinematics_validation.py`)
- **Purpose**: Validate printer's kinematic configuration and movement system
- **Category**: Configuration
- **Duration**: 2-5 minutes (estimated)
- **Dependencies**: safety
- **Description**: Checks if kinematics type matches actual printer, validates motor configuration, tests coordinate calculations

### 9. Lighting Test (`lighting_test.py`)
- **Purpose**: Test printer lighting systems and status indicators
- **Category**: Accessories
- **Duration**: 2-5 minutes (estimated)
- **Dependencies**: safety
- **Description**: Tests chamber lights, status LEDs, RGB lighting systems if configured

## Test Base Class System

### BaseTest Abstract Class (`base_test.py`)
All tests inherit from `BaseTest` which provides:

#### Core Methods (Must be implemented):
- `get_name()` - Human-readable test name
- `get_description()` - Test description for UI
- `_run_test()` - Main test execution logic (async)

#### Optional Methods:
- `get_dependencies()` - List of test IDs that must pass first
- `is_applicable()` - Check if test applies to current printer config
- `get_ui_config()` - Dynamic UI configuration for user interactions

#### Test Lifecycle:
- `NOT_STARTED` → `RUNNING` → `PASSED`/`FAILED`/`ERROR`
- Status callbacks update UI in real-time
- Progress callbacks (0-100%) show test advancement
- User prompt callbacks handle interactive elements

#### User Interaction Types:
- `YES_NO` - Simple yes/no questions
- `MULTIPLE_CHOICE` - Multiple options
- `TEXT_INPUT` - Text entry
- `CONFIRMATION` - Acknowledge/continue prompts
- `INSTRUCTION` - Display instructions to user

## PrinterTestsModule Integration

### Core Manager Integration (`printer_tests_module.py`)
The **PrinterTestsModule** serves as the bridge between individual tests and the core system:

#### Key Responsibilities:
1. **Dynamic Test Discovery**: Scans `printer_tests/` directory for classes inheriting from BaseTest
2. **State Management**: Updates commissioning state via StateManager
3. **Event Communication**: Publishes test events via EventBus
4. **Test Execution**: Manages running tests with unique run_ids
5. **Mock System**: Provides MockPrinterManager and MockConfigParser for testing

#### Integration Points:
- **EventBus**: Subscribes to `commissioning_request` and `test_user_response` events
- **StateManager**: Maintains `commissioning.active`, `commissioning.current_test`, `commissioning.available_tests`
- **Callbacks**: Provides progress, status, and user_prompt callbacks that publish events

#### Test Instance Management:
- Creates test instances with proper callbacks
- Tracks running tests by run_id
- Stores test results for status queries
- Prevents duplicate test execution

## Core Manager Architecture (`manager.py`)

### PrinterBuddyCore Class
Central coordinator managing the entire system:

#### Module Registration:
- Registers PrinterTestsModule with core system
- Connects modules to EventBus for inter-module communication
- Maintains module state in StateManager

#### Log Collection:
- **UILogHandler**: Custom logging handler captures all Python log messages
- Stores recent messages in circular buffer (max 1000)
- Provides filtered log access for web UI console
- Formats logs with timestamp, level, and source information

#### Event & State Coordination:
- **EventBus**: Publish/subscribe system for loose module coupling
- **StateManager**: Centralized state storage and retrieval
- **Module Updates**: Broadcasts state changes between modules
- **API Integration**: Notifies API server of state changes for UI updates

## API Server Integration (`server.py`)

### HTTP REST Endpoints
The API server exposes test functionality to the web UI:

#### Test-Related Endpoints:
- `GET /api/commissioning/tests` - List available tests
- `GET /api/commissioning/status` - Current commissioning status
- `GET /api/commissioning/ui-config/{test_id}` - Dynamic UI config for test
- `POST /api/commissioning/start` - Start a test
- `POST /api/commissioning/stop` - Stop commissioning
- `POST /api/commissioning/respond` - Submit user response to test

#### System Endpoints:
- `GET /api/status` - Overall system status
- `GET /api/state` - Current system state
- `GET /api/logs/stream` - Real-time log streaming for console

### Real-Time Communication:
- HTTP polling for status updates (WebSocket planned)
- Event broadcasting to connected clients
- Dynamic UI configuration based on test state

## Current Status & Implementation Notes

### Completed Features:
- ✅ Test discovery system working (9 tests discovered)
- ✅ Base test class architecture complete
- ✅ Core manager integration functional
- ✅ API endpoints implemented
- ✅ Log collection and UI console working
- ✅ Mock printer manager for testing

### In Development:
- 🔄 Individual test implementations (currently placeholders)
- 🔄 Real Moonraker integration (currently using mocks)
- 🔄 WebSocket support for real-time updates
- 🔄 Advanced user interaction handling

### Future Enhancements:
- Integration with actual Klipper/Moonraker APIs
- Persistent test result storage
- Test scheduling and automation
- Advanced printer configuration validation
- Integration with printer-specific test suites