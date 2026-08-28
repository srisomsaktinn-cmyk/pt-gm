@echo off
set "PATH=C:\Windows\System32;C:\Windows;%PATH%"
cd /d D:\Kaeha

echo ================================================================================
echo Starting Strategy V2.6 Multi-Asset MT5 Paper Trader (5 Assets)...
echo ================================================================================

python execute_multi_asset_paper_trader.py
if errorlevel 1 (
    echo.
    echo [ERROR] Python failed to start. Trying with py launcher...
    py execute_multi_asset_paper_trader.py
)

pause
