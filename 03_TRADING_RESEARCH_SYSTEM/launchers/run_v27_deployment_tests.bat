@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Running Strategy V2.7 Demo Deployment Safety Verification Tests...
echo ================================================================================

python execute_v27_deployment_tests.py
pause
