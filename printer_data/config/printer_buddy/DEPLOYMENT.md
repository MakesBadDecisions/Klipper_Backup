# Printer Buddy - Raspberry Pi Deployment Checklist

## ✅ Pre-Deployment Validation

### 🔍 Code Review Completed
- [x] **MoonrakerPrinterManager**: Full Moonraker API integration implemented
- [x] **MoonrakerConfigParser**: Jinja2-aware config parsing via Moonraker  
- [x] **Hardware Detection**: Auto-detection with graceful fallback
- [x] **Error Handling**: Robust timeout and retry logic
- [x] **Session Management**: Proper aiohttp session lifecycle
- [x] **API Endpoints**: Validated against official Moonraker documentation

### 📋 Dependencies Required on Pi
```bash
# Python packages needed (install via pip)
aiohttp          # HTTP client for Moonraker API  
asyncio          # Already in Python 3.7+
configparser     # Already in Python standard library
pathlib          # Already in Python 3.4+
```

### 🔧 System Requirements
- **Python 3.7+** (Klipper systems typically have 3.9+)
- **Klipper + Moonraker running** on port 7125
- **Network access** between Printer Buddy and Moonraker
- **Write permissions** to printer_data/config/ directory

## 🚀 Deployment Steps

### 1. File Transfer
Copy entire `printer_buddy/` directory to Raspberry Pi:
```bash
# From your Windows machine:
scp -r printer_data/config/printer_buddy/ pi@your-pi-ip:/home/pi/printer_data/config/

# Or use WinSCP, FileZilla, or VS Code Remote SSH
```

### 2. Verify Klipper Integration
Ensure `printer.cfg` contains:
```ini
[include printer_buddy/printer_buddy.cfg]
```

### 3. Install Dependencies (if needed)
```bash
# SSH to Raspberry Pi
ssh pi@your-pi-ip

# Install aiohttp if not present
pip3 install aiohttp

# Or use the Klipper virtual environment
~/klippy-env/bin/pip install aiohttp
```

### 4. Test Scripts
```bash
cd /home/pi/printer_data/config/printer_buddy

# Test with production auto-detection
python3 start_printer_buddy.py

# Or use specific modes
python3 start_development.py    # Mock mode
python3 start_hardware_test.py  # Force real hardware
```

## 🔍 Testing Checklist

### ✅ Basic Functionality
- [ ] **Auto-detection works**: Script detects Moonraker and uses real hardware
- [ ] **Mock fallback works**: If Moonraker unavailable, falls back to mock
- [ ] **API server starts**: http://raspberry-pi-ip:8080 accessible
- [ ] **Web UI loads**: Interface displays properly
- [ ] **Test discovery**: Safety Validation test appears in UI

### ✅ Real Hardware Integration
- [ ] **Printer status**: Real temperature readings appear
- [ ] **GCode commands**: Commands sent via UI affect actual printer
- [ ] **Error handling**: Network issues handled gracefully
- [ ] **Config parsing**: Jinja2 templates processed correctly

### ✅ Safety Validation
- [ ] **Emergency stop works**: Can halt printer via UI
- [ ] **State validation**: Printer must be in 'ready' state for tests
- [ ] **Error states handled**: System responds to printer errors
- [ ] **Connection loss**: Graceful handling of Moonraker disconnection

## 🐛 Troubleshooting Guide

### Issue: "ModuleNotFoundError: No module named 'aiohttp'"
**Solution**: Install aiohttp in the correct Python environment
```bash
~/klippy-env/bin/pip install aiohttp
# or
python3 -m pip install aiohttp
```

### Issue: "Moonraker not found at http://localhost:7125"
**Solutions**:
1. Check Moonraker is running: `systemctl status moonraker`
2. Verify port: Check `moonraker.conf` for actual port
3. Use custom URL: `python3 start_printer_buddy.py --moonraker-url http://localhost:7125`
4. Check firewall: Ensure port 7125 is accessible

### Issue: "Config parsing errors with Jinja2 templates"
**Expected**: MoonrakerConfigParser should handle this automatically
**If fails**: Check logs, may need to update Moonraker or restart service

### Issue: "Web UI shows mock data in real hardware mode"
**Check**: 
1. Console logs show "REAL HARDWARE" mode
2. Temperature readings change with actual printer
3. GCode commands in UI affect real printer

### Issue: "Permission denied writing to config directory"  
**Solution**: Ensure proper file ownership
```bash
sudo chown -R pi:pi /home/pi/printer_data/config/printer_buddy
chmod -R 755 /home/pi/printer_data/config/printer_buddy
```

## 📝 Post-Deployment Validation

### 🔄 Smoke Tests
1. **Start system**: `python3 start_printer_buddy.py`
2. **Check logs**: Look for "REAL HARDWARE" mode confirmation
3. **Access UI**: Open http://pi-ip:8080 in browser
4. **View printer data**: Confirm real temperature readings
5. **Test safety stop**: Emergency stop button should work
6. **Run a test**: Safety Validation should execute

### 📊 Performance Verification
- API responses < 2 seconds
- UI loads within 5 seconds  
- Real-time data updates working
- No memory leaks over extended operation

## 🔒 Security Notes
- **Network Access**: Printer Buddy runs on port 8080 (unsecured)
- **Printer Control**: Full GCode access - ensure network security
- **Config Access**: Can read all printer configuration
- **Consider**: Run behind reverse proxy for production use

## 📞 Support Information
- **Logs Location**: Console output and potential log files
- **Config Files**: `/home/pi/printer_data/config/printer_buddy/`
- **Moonraker Logs**: `/home/pi/printer_data/logs/moonraker.log`
- **Klipper Logs**: `/home/pi/printer_data/logs/klippy.log`

## 🎯 Success Criteria
✅ **Deployment Successful When**:
1. Auto-detection correctly identifies real hardware
2. Web UI shows actual printer temperatures and status
3. GCode commands sent through UI control real printer
4. Safety Validation test can be started and shows real responses
5. System handles Moonraker disconnections gracefully
6. No Python errors in startup or operation