@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Starting Strategy V2.7 Multi-Asset Forward Paper Trader (DEMO ONLY)...
echo ================================================================================

python -m rsi_trend_pullback.mt5_v27_paper_trader
pause
