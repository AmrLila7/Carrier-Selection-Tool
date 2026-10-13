@echo off
chcp 65001 > nul
title Carrier ClassiCOOL Engineering Suite
echo Launching Carrier Selection Tool...

:: Move to the folder where the .bat is located
cd /d "%~dp0"

:: Run the script using a relative path to avoid Arabic encoding issues in arguments
"C:\Users\amrli\AppData\Local\Python\pythoncore-3.14-64\python.exe" "src\carrier_tool\main.py"

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] The application failed to start.
)
pause
