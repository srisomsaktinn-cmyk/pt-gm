@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Running Strategy V2.7 Master Robustness, Cost Stress & Untouched OOS Suite...
echo ================================================================================

python execute_v27_robustness_suite.py
pause
