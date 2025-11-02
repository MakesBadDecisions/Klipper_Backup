@echo off
REM Production Mode - Smart Auto-Detection
REM Tries real hardware, falls back to mock

echo ========================================
echo   PRINTER BUDDY - PRODUCTION MODE
echo ========================================
echo  Smart auto-detection
echo  Tries real hardware, falls back to mock
echo  Best for normal usage
echo ========================================
echo.

cd /d "%~dp0"
python start_printer_buddy.py

echo.
pause