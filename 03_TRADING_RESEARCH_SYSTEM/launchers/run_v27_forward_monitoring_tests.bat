@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Running Strategy V2.7 Forward Monitoring & Telemetry Infrastructure Tests...
echo ================================================================================

python execute_v27_forward_monitoring_tests.py
pause
