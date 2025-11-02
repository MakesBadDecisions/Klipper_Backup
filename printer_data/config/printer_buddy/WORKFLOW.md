# Printer Buddy - Workflow Guide

This guide explains the different ways to start Printer Buddy for different use cases.

## Quick Start (Batch Files)

Double-click the appropriate batch file for your needs:

### 🔧 `dev.bat` - Development Mode
- **Always uses mock hardware**
- Safe for UI development and testing
- No printer connection required
- Perfect for code changes and experimentation

### 🖨️ `test.bat` - Hardware Test Mode  
- **Always uses real hardware**
- Requires Moonraker connection
- For actual printer testing and commissioning
- **Warning prompt before starting**

### 🚀 `production.bat` - Production Mode
- **Smart auto-detection**
- Tries real hardware first, falls back to mock
- Best for normal usage
- Automatic and hassle-free

## Manual Scripts

You can also run the Python scripts directly:

### Development (Mock Hardware)
```powershell
python start_development.py
```

### Hardware Testing (Real Hardware)
```powershell
python start_hardware_test.py
python start_hardware_test.py --moonraker-url http://192.168.1.100:7125
```

### Production (Auto-Detect)
```powershell
python start_printer_buddy.py                    # Auto-detect
python start_printer_buddy.py --hardware mock    # Force mock
python start_printer_buddy.py --hardware real    # Force real
```

## Workflow Recommendations

### 🎯 For UI Development
Use `dev.bat` or `start_development.py`:
- Instant startup, no hardware needed
- Safe to experiment with tests and features
- All printer operations are simulated

### 🔧 For Printer Testing  
Use `test.bat` or `start_hardware_test.py`:
- Direct connection to real printer
- All operations affect actual hardware
- Use when commissioning or validating printer

### ⚡ For Normal Usage
Use `production.bat` or `start_printer_buddy.py`:
- Automatically detects if printer is connected
- Falls back gracefully to mock mode
- Best of both worlds

## Technical Details

### Hardware Detection
The production script attempts to connect to Moonraker at:
- Default: `http://localhost:7125`
- Custom: Use `--moonraker-url` parameter

### Mock vs Real Hardware
- **Mock**: Simulated responses, safe development
- **Real**: Direct Moonraker API calls, actual printer control

### Architecture
All modes use the same core system with different hardware managers:
- `MockPrinterManager`: Simulated printer responses
- `MoonrakerPrinterManager`: Real Moonraker API integration

## Troubleshooting

### "Moonraker not found" 
- Check if Klipper/Moonraker is running
- Verify Moonraker URL and port
- Use `--moonraker-url` to specify custom address

### Mock mode when expecting real hardware
- Check Moonraker is accessible at specified URL
- Use `start_hardware_test.py` to force real hardware mode
- Verify firewall/network settings

### Import errors or missing modules
- Ensure all dependencies are installed
- Check Python path includes printer_buddy directory
- Verify virtual environment is activated if using one