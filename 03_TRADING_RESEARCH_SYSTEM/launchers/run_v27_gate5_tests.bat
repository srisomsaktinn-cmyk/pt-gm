@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Running Strategy V2.7 Gate 5 Final Integrity Audit Unit Tests...
echo ================================================================================

python execute_v27_gate5_tests.py
pause
