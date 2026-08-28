@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Launching Strategy V2.7 Master Quantitative Research & Engineering Pipeline...
echo ================================================================================

python execute_v27_master_research_pipeline.py
pause
