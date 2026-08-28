@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Running Strategy V2.7 Missed Signal Economic Value Analysis...
echo ================================================================================

python execute_missed_economic_analysis.py
pause
