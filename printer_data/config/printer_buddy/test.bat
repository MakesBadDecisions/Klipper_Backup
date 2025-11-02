@echo off
REM Hardware Test Mode - Always Real Hardware
REM For actual printer testing and commissioning

echo ========================================
echo   PRINTER BUDDY - HARDWARE TEST MODE
echo ========================================
echo  REAL HARDWARE - Controls actual printer
echo  Moonraker connection required
echo  Use for actual printer testing only
echo ========================================
echo.
echo WARNING: This will control real hardware!
echo Make sure printer is safe and ready.
echo.
set /p confirm="Continue? (y/N): "
if /i not "%confirm%"=="y" (
    echo Cancelled.
    pause
    exit /b
)

cd /d "%~dp0"
python start_hardware_test.py

echo.
pause