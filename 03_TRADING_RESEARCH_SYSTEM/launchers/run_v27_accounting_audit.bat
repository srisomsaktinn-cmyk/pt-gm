@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Running Strategy V2.7 Post-Backtest Accounting & Attribution Audit...
echo ================================================================================

python execute_v27_accounting_audit.py
pause
