@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Starting Strategy V2.6 Single-Asset MT5 Paper Trader (XAUUSD)...
echo ================================================================================

python rsi_trend_pullback/mt5_paper_trader.py
if errorlevel 1 (
    echo.
    echo [ERROR] Python failed to start. Trying with py launcher...
    py rsi_trend_pullback/mt5_paper_trader.py
)

pause
