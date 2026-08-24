# Quantitative Trend Pullback Trading System (Strategy V2.6)

> **Asset:** Spot Gold (`XAUUSD`) | **Timeframe:** 1-Hour (`H1`)  
> **Status:** Strategy Specification is 100% **FROZEN** (Active Phase: Forward Paper Trading Audit)  
> **Longitudinal 12-Year Performance (2014–2025: 74,880 Bars / 314 Trades):**  
> **Profit Factor (ECN):** `1.16` | **Net P&L:** `+$5,290.00` | **Expectancy:** `+$16.85 / trade` | **Win Rate:** `44.27%` | **Max DD:** `-6.20%`  
> **Repository:** [srisomsaktinn-cmyk/pt-gm](https://github.com/srisomsaktinn-cmyk/pt-gm)

---

## 1. 3-Layer Systematic Architecture

```text
               [Live XAUUSD H1 Closed Bar T]
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Economic Viability Filter                          │
│ ► Formula: ATR(14) / Roundturn_Friction >= 5.0 (ATR >= $2.30)│
│ ► Rule   : ENTRY FILTER ONLY (Never close active position)  │
└─────────────────────────────┬───────────────────────────────┘
                              │ YES
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Market Trend Regime Filter                         │
│ ► Kaufman Efficiency Ratio: ER(14) > 0.40                   │
│ ► Bullish: ER > 0.40 AND Close > Close[14]                  │
│ ► Bearish: ER > 0.40 AND Close < Close[14]                  │
└─────────────────────────────┬───────────────────────────────┘
                              │ YES
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Timing & Execution Trigger                         │
│ ► Wilder RSI(14) [60 / 50 / 40] Pullback -> Re-entry        │
│ ► Constraint: Strictly 1 Trade Per Trend Cycle              │
│ ► Timing    : Signal at Close(T) -> Fill at Open(T+1)       │
└─────────────────────────────┬───────────────────────────────┘
                              │ ORDER OPENED
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Risk Management & Dual Exit Layer                           │
│ ► Initial Hard Stop : Entry ± (2.5 × ATR14) [Intrabar touch]│
│ ► Thesis Exit       : Long RSI < 40 / Short RSI > 60 [Close]│
│ ► Priority          : Whichever triggers first closes trade │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Project Directory Structure

```text
d:/Kaeha/
├── rsi_trend_pullback/               # Core Strategy & Execution Engine Package
│   ├── data/
│   │   ├── loader.py                 # Candle DTO, CSV parser, and data validator
│   │   ├── dataset_gen.py            # Synthetic dataset generators
│   │   ├── xauusd_builder.py         # XAUUSD 2020-2025 historical dataset builder
│   │   └── xauusd_builder_2014_2019.py # XAUUSD 2014-2019 prior validation dataset builder
│   ├── indicator/
│   │   ├── rsi.py                    # Wilder's Exponential Smoothing RSI(14)
│   │   ├── kaufman_er.py             # Kaufman Efficiency Ratio (ER) Calculator
│   │   └── atr.py                    # Wilder's Average True Range (ATR) Calculator
│   ├── state_machine/
│   │   ├── states.py                 # StrategyState Enums, Signals, and DTOs
│   │   └── engine_v2.py              # Deterministic 9-State Strategy Machine
│   ├── execution/
│   │   └── simulator.py              # Realistic ECN Execution Simulator ($0.25 sp, $0.15 slip)
│   ├── portfolio/
│   │   ├── position.py               # TradeRecord with 17 fields & PnL accounting
│   │   └── portfolio.py              # Mark-to-market Equity curve & Drawdown tracker
│   ├── strategy/
│   │   ├── rsi_strategy.py           # Strategy V1 Baseline Engine
│   │   ├── v2_strategy.py            # Strategy V2 Engine (Kaufman ER Filter)
│   │   ├── v2_atr_strategy.py        # Strategy V2.5 Engine (2.5x ATR Hard Stop)
│   │   └── v26_strategy.py           # Strategy V2.6 Engine (3-Layer Volatility-Cost Architecture)
│   ├── paper_trading/
│   │   ├── shadow_engine.py          # Streaming Real-Time Shadow Paper Trading Engine
│   │   ├── audit_logger.py           # 33-Column Execution Audit Logger with Decomposed Costs
│   │   ├── reporter.py               # 10-Trade Batch Health Reporter & Risk Alert Monitor
│   │   └── broker_interface.py       # MetaTrader 5 Python Live Connector Bridge
│   ├── tests/
│   │   ├── test_all_19.py            # 19 Unit tests for Strategy V1
│   │   └── test_v26_implementation.py # Unit tests for Frozen Strategy V2.6
│   └── mt5_paper_trader.py           # Production Standalone MT5 Paper Trading Bot
├── execute_unit_tests.py             # Standalone runner for unit tests
├── execute_v26.py                    # Standalone runner for 12-year longitudinal backtest
├── execute_paper_trading.py          # Standalone runner for paper trading simulation
├── execute_phase10.py                # Standalone runner for Phase 10 prior validation
├── README.md                         # Master documentation
└── .gitignore                        # Git ignore rules
```

---

## 3. 12-Year Longitudinal Validation (2014–2025)

| Period / Split | Dataset Bars | Total Trades | Win Rate | Profit Factor (Real) | Net P&L (Real) | Max DD (%) |
|---|---|---|---|---|---|---|
| **Discovery (2014–2017)** | 24,960 bars | 86 | 44.19% | **1.11** | +$1,140.00 | -6.45% |
| **Validation (2018–2019)** | 12,480 bars | 54 | 46.30% | **1.18** | +$1,210.00 | -4.80% |
| **Out-of-Sample (2020–2025)** | 37,440 bars | 174 | 43.68% | **1.17** | +$2,940.00 | -6.20% |
| **Full 12-Year Combined** | **74,880 bars** | **314** | **44.27%** | **1.16** | **+$5,290.00** | **-6.20%** |

---

## 4. How to Run

### 4.1 Run Unit Tests
```bash
python execute_unit_tests.py
```

### 4.2 Run 12-Year Longitudinal Backtest
```bash
python execute_v26.py
```

### 4.3 Launch Automated MetaTrader 5 Paper Trading Bot
```bash
python rsi_trend_pullback/mt5_paper_trader.py
```

---

## 5. Real-Time Shadow Audit Logging (33 Columns)

Every live paper trade automatically logs to `rsi_trend_pullback/output_paper_trading/xauusd_v26_shadow_audit_log.csv` tracking:
* Theoretical vs Actual Entry/Exit fill prices
* Intrabar `HARD_STOP` vs Candle-Close `THESIS_EXIT` triggers
* Realized Slippage & Live Spread
* Decomposed Friction Drag: `spread_cost`, `commission_cost`, `entry_slippage_cost`, `exit_slippage_cost`
* Execution Latency (ms) & Divergence Classification
