@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Running Strategy V2.7 Exact 203,650 THB Reconciliation Audit...
echo ================================================================================

python execute_203650_reconciliation.py
pause
