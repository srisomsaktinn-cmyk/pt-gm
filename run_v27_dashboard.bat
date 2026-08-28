@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Launching Strategy V2.7 Live Forward Telemetry and Health Dashboard...
echo ================================================================================

python 03_TRADING_RESEARCH_SYSTEM\runners\v27_forward_dashboard.py
pause
