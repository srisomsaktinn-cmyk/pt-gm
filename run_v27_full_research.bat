@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Launching Strategy V2.7 Master Quantitative Research and Engineering Pipeline...
echo ================================================================================

python 03_TRADING_RESEARCH_SYSTEM\runners\execute_v27_master_research_pipeline.py
pause
