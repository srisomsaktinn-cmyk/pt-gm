@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Running Strategy V2.7 Deep Performance Forensics & Unit-NAV Audit...
echo ================================================================================

python execute_v27_forensics.py
pause
