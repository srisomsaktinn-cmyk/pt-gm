@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Running Strategy V2.7 Gate 1 Pyramiding Math & Risk Proof Unit Tests...
echo ================================================================================

python execute_v27_gate1_tests.py
pause
