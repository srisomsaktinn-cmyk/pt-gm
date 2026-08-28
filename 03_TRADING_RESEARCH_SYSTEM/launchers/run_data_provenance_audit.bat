@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Running Strategy V2.7 Critical Data Provenance & Bar Count Audit...
echo ================================================================================

python execute_data_provenance_audit.py
pause
