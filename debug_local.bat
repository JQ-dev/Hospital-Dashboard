@echo off
REM Quick launcher for Windows - Debug Mode
REM Simulates Render deployment environment locally

echo ================================================================================
echo LOCAL DEBUG MODE - Simulating Render Deployment (Windows)
echo ================================================================================
echo.

REM Set environment variables for local debugging
set DEBUG=true
set PORT=8050
set HOST=0.0.0.0
set DATABASE_PATH=data/auth.db

echo Configuration:
echo   DEBUG: %DEBUG%
echo   HOST: %HOST%
echo   PORT: %PORT%
echo   DATABASE_PATH: %DATABASE_PATH%
echo.
echo Server will start at: http://localhost:%PORT%
echo Press Ctrl+C to stop the server
echo ================================================================================
echo.

REM Run the debug launcher
python debug_local.py

pause
