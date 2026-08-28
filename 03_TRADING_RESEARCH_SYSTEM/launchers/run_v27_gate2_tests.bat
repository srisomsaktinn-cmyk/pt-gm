@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Running Strategy V2.7 Gate 2 Portfolio Heat & Collision Unit Tests...
echo ================================================================================

python execute_v27_gate2_tests.py
pause
