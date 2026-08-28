# Quantitative Trend Pullback Trading System (Strategy V2.6)

> **Core Asset:** Spot Gold (`XAUUSD`) | **Multi-Asset Universe (Top 5):** `XAUUSD`, `USDJPY`, `GBPUSD`, `US500`, `BTCUSD`  
> **Timeframe:** 1-Hour (`H1`)  
> **Status:** Strategy Specification is 100% **FROZEN** (Active Phase: Forward Paper Trading Audit)  
> **12-Year Longitudinal Backtest (XAUUSD H1 2014–2025: 74,880 Bars / 314 Trades):**  
> **Profit Factor (ECN):** `1.16` | **Net P&L:** `+$5,290.00` | **Expectancy:** `+$16.85 / trade` | **Win Rate:** `44.27%` | **Max DD:** `-6.20%`  
> **Multi-Asset Portfolio (Top 5 Assets 2020–2025: 996 Trades):**  
> **Profit Factor (ECN):** `1.19` | **Net P&L:** `+$16,170.00` | **Win Rate:** `45.28%` | **Max DD:** `-7.40%`  
> **Repository:** [srisomsaktinn-cmyk/pt-gm](https://github.com/srisomsaktinn-cmyk/pt-gm)

---

## 1. 3-Layer Systematic Architecture (100% Frozen)

```text
               [Live Closed H1 Bar T]
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Economic Viability Filter                          │
│ ► Formula: ATR(14) / Roundturn_Friction >= 5.0              │
│ ► Rule   : ENTRY FILTER ONLY (Never close active position)  │
└────────────────────────┬────────────────────────────────────┘
                         │ YES
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Market Trend Regime Filter                         │
│ ► Kaufman Efficiency Ratio: ER(14) > 0.40                   │
│ ► Bullish: ER > 0.40 AND Close > Close[14]                  │
│ ► Bearish: ER > 0.40 AND Close < Close[14]                  │
└────────────────────────┬────────────────────────────────────┘
                         │ YES
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Timing & Execution Trigger                         │
│ ► Wilder RSI(14) [60 / 50 / 40] Pullback -> Re-entry        │
│ ► Constraint: Strictly 1 Trade Per Trend Cycle              │
│ ► Timing    : Signal at Close(T) -> Fill at Open(T+1)       │
└────────────────────────┬────────────────────────────────────┘
                         │ ORDER OPENED
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Risk Management & Dual Exit Layer                           │
│ ► Initial Hard Stop : Entry ± (2.5 × ATR14) [Intrabar touch]│
│ ► Thesis Exit       : Long RSI < 40 / Short RSI > 60 [Close]│
│ ► Dynamic Sizing    : Balanced Profile (3.0% Auto-Risk)     │
│ ► Priority          : Whichever triggers first closes trade │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Project Directory Structure

```text
d:/Kaeha/
├── rsi_trend_pullback/                     # Core Strategy & Execution Package
│   ├── data/
│   │   ├── loader.py                       # Candle DTO, CSV parser, and data validator
│   │   ├── dataset_gen.py                  # Synthetic dataset generators
│   │   ├── xauusd_builder.py               # XAUUSD 2020-2025 historical dataset builder
│   │   ├── xauusd_builder_2014_2019.py     # XAUUSD 2014-2019 prior validation dataset builder
│   │   ├── xauusd_m15_builder.py           # XAUUSD M15 dataset builder
│   │   └── multi_asset_builder.py          # Multi-Asset H1 historical dataset builder
│   ├── indicator/
│   │   ├── rsi.py                          # Wilder's Exponential Smoothing RSI(14)
│   │   ├── kaufman_er.py                   # Kaufman Efficiency Ratio (ER) Calculator
│   │   └── atr.py                          # Wilder's Average True Range (ATR) Calculator
│   ├── state_machine/
│   │   ├── states.py                       # StrategyState Enums, Signals, and DTOs
│   │   └── engine_v2.py                    # Deterministic 9-State Strategy Machine
│   ├── execution/
│   │   └── simulator.py                    # Realistic ECN Execution Simulator ($0.25 sp, $0.15 slip)
│   ├── portfolio/
│   │   ├── position.py                     # TradeRecord with 17 fields & PnL accounting
│   │   └── portfolio.py                    # Mark-to-market Equity curve & Drawdown tracker
│   ├── strategy/
│   │   ├── rsi_strategy.py                 # Strategy V1 Baseline Engine
│   │   ├── v2_strategy.py                  # Strategy V2 Engine (Kaufman ER Filter)
│   │   ├── v2_atr_strategy.py              # Strategy V2.5 Engine (2.5x ATR Hard Stop)
│   │   └── v26_strategy.py                 # Strategy V2.6 Engine (3-Layer Volatility-Cost Architecture)
│   ├── paper_trading/
│   │   ├── shadow_engine.py                # Streaming Real-Time Shadow Paper Trading Engine
│   │   ├── audit_logger.py                 # 33-Column Execution Audit Logger with Decomposed Costs
│   │   ├── reporter.py                     # 10-Trade Batch Health Reporter & Risk Alert Monitor
│   │   └── broker_interface.py             # MetaTrader 5 Python Live Connector Bridge
│   ├── tests/
│   │   ├── test_all_19.py                  # 19 Unit tests for Strategy V1
│   │   └── test_v26_implementation.py      # Full 8-Dimension Unit Tests for Frozen Strategy V2.6
│   ├── missed_signal_scanner.py            # Historical Schedule Availability Scanner
│   ├── check_overnight_missed_trades.py    # Live Overnight Missed Trade Checker
│   ├── mt5_paper_trader.py                 # Single-Asset MT5 Paper Trading Bot (XAUUSD)
│   └── mt5_multi_asset_paper_trader.py     # Multi-Asset MT5 Paper Trading Bot (5 Assets)
├── execute_unit_tests.py                   # Standalone runner for 8-dimension unit tests
├── execute_v26.py                          # Standalone runner for 12-year longitudinal backtest
├── execute_multi_asset_paper_trader.py     # Standalone runner for multi-asset paper trader
├── execute_check_missed_trades.py          # Standalone runner for overnight missed trades check
├── execute_compounding_experiment.py       # Standalone runner for compounding risk experiment
├── execute_thb_simulation.py               # Standalone runner for 1-Year THB DCA simulation
├── run_bot.bat                             # 1-Click launcher for Single-Asset Bot
├── run_multi_bot.bat                       # 1-Click launcher for Multi-Asset Bot (Top 5 Assets)
├── check_missed_trades.bat                 # 1-Click launcher for Overnight Missed Trade Audit
├── README.md                               # Master project documentation
└── .gitignore                              # Git exclusion rules
```

---

## 3. Top 5 Screened Multi-Asset Portfolio (2020–2025: H1)

| Symbol | Asset Class | Total Trades | Monthly Freq | Win Rate | Profit Factor (ECN) | Net P&L (6 Yrs) | Max DD (%) |
|---|---|---|---|---|---|---|---|
| **`US500`** | Equity Index CFD | 210 | 2.9 / mo | 47.1% | **1.25** | **+$4,220.00** | -6.50% |
| **`USDJPY`** | Forex Major | 196 | 2.7 / mo | 46.4% | **1.22** | **+$3,680.00** | -5.10% |
| **`BTCUSD`** | Crypto Asset | 248 | 3.4 / mo | 42.7% | **1.18** | **+$3,180.00** | -9.80% |
| **`XAUUSD`** | Spot Gold | 174 | 2.4 / mo | 43.7% | **1.17** | **+$2,940.00** | -6.20% |
| **`GBPUSD`** | Forex Major | 168 | 2.3 / mo | 44.0% | **1.14** | **+$2,150.00** | -5.80% |
| **Combined**| **5-Asset Portfolio** | **996** | **~13.8 / mo** | **45.28%** | **1.19** | **+$16,170.00** | **-7.40%** |

---

## 4. How to Run

### 4.1 Launch Multi-Asset MT5 Paper Trading Bot (5 Assets)
Double-click `run_multi_bot.bat` or run:
```bash
python execute_multi_asset_paper_trader.py
```

### 4.2 Check Overnight Missed Trades (Last 24 Hours)
Double-click `check_missed_trades.bat` or run:
```bash
python rsi_trend_pullback/check_overnight_missed_trades.py
```

### 4.3 Run 8-Dimension Unit Test Suite
```bash
python execute_unit_tests.py
```
