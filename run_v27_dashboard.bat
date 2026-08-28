@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Launching Strategy V2.7 Live Forward Telemetry & Health Dashboard...
echo ================================================================================

python v27_forward_dashboard.py
pause
