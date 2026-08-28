@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Running Strategy V2.7 Personal Schedule & Opportunity Coverage Audit...
echo ================================================================================

python execute_personal_coverage_analysis.py
pause
