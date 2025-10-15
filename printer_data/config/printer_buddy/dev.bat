@echo off
REM Development Mode - Always Mock Hardware
REM Perfect for UI development, testing, and safe experimentation

echo ========================================
echo    PRINTER BUDDY - DEVELOPMENT MODE
echo ========================================
echo  Safe mock hardware for development
echo  No real printer connection required
echo  Perfect for UI work and testing
echo ========================================
echo.

cd /d "%~dp0"
python start_development.py

echo.
pause