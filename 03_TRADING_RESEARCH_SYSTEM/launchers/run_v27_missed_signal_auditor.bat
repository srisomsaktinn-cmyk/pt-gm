@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Running Strategy V2.7 Offline Missed Signal Auditor...
echo ================================================================================

python execute_missed_signal_audit.py
pause
