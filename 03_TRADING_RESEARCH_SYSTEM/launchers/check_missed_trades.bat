@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Checking Overnight Missed Trades (Last 24 Hours)...
echo ================================================================================

python rsi_trend_pullback/check_overnight_missed_trades.py
pause
