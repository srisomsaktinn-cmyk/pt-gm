@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Running Strategy V2.7 Gate 4 Broker Sizing & Micro-Lot Unit Tests...
echo ================================================================================

python execute_v27_gate4_tests.py
pause
