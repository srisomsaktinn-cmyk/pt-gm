@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Running Strategy V2.7 Component Ablation Study Matrix...
echo ================================================================================

python execute_v27_ablation_study.py
pause
