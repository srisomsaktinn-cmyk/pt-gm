@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Scanning MT5 for Overnight and Offline Missed Signals (Last 24-48 Hours)...
echo ================================================================================

python rsi_trend_pullback\check_overnight_missed_trades.py
pause
