@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Running Strategy V2.7 Independent Reference Quantitative Validator...
echo ================================================================================

python execute_independent_validation.py
pause
