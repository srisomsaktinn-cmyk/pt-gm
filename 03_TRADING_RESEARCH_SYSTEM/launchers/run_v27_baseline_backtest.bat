@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Running Strategy V2.7 Official Baseline Backtest (2020-2025: 6 Full Years)...
echo ================================================================================

python execute_v27_baseline_backtest.py
pause
