@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Running Strategy V2.7 Research & Forward Analytics Center Test Suite...
echo ================================================================================

python execute_analytics_center_tests.py
pause
