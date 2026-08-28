@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Running Strategy V2.7 Gate 3 Multi-Asset Independent Calendar Unit Tests...
echo ================================================================================

python execute_v27_gate3_tests.py
pause
