@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Running Strategy V2.7 Missed Signal Tail-Value & Top-Winner Analysis...
echo ================================================================================

python execute_tail_value_analysis.py
pause
