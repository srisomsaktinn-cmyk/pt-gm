# 📘 PROJECT_CONTEXT.md: Master Single Source of Truth (SSOT)

> **Authoritative Project Specification & Synchronization Document**  
> **Repository:** [srisomsaktinn-cmyk/pt-gm](https://github.com/srisomsaktinn-cmyk/pt-gm)  
> **Last Synchronized:** 2026-08-28 (Asia/Bangkok UTC+7)  
> **Purpose:** This document is the absolute single source of truth for all human developers, LLM models (Gemini, Claude, GPT), and automated execution agents. No assumptions outside this document are permitted.

---

## 1. PROJECT GOVERNANCE & ACTIVE STATUS

| Item | Current Status | Enforcement Policy |
|---|---|---|
| **Strategy V2.6** | 🔒 **100% FROZEN** | Zero parameter tweaking. Zero indicator additions. Production standard. |
| **Strategy V2.7** | 🔬 **RESEARCH CANDIDATE ONLY** | Confined strictly to laboratory backtests/experiments. Not deployed to live. |
| **Current Project Phase** | **Phase 11: Multi-Asset Live Paper Trading Audit** | Forward execution on XM Global MT5 Ultra Low Demo. |
| **Execution Protocol** | **Zero Look-Ahead / Causal Streaming** | Signal on $Close(T) \rightarrow$ Execution on $Open(T+1) \pm \text{Slippage}$. |

---

## 2. AUTHORITATIVE RISK HIERARCHY & TAXONOMY

All risk metrics, limits, and rules must be explicitly classified into one of the following 5 distinct categories:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          5-TIER RISK GOVERNANCE TAXONOMY                               │
│                                                                                        │
│   1. [PERSONAL CONSTRAINT]    ► 25.0% Max Acceptable Drawdown (Hard Upper Boundary)   │
│   2. [MONITORING THRESHOLD]   ► 20.0% Serious Risk Review | 15.0% Elevated Risk Review │
│   3. [STATISTICAL REFERENCE]  ► 11.8% Monte Carlo 95th Percentile | 6.2% Historical DD │
│   4. [PORTFOLIO RISK RULE]    ► Max 2 Concurrent Positions | Dynamic Heat Calculation  │
│   5. [STRATEGY RULE]          ► 3.0% Balanced Dynamic Risk per Trade | 2.5x ATR SL    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Explicit Risk Boundaries:
1. **`[PERSONAL CONSTRAINT]` 25% Maximum Acceptable Account Drawdown:**
   - This is the user's **Hard Upper Risk Boundary**.
   - It is NOT a target drawdown, NOT a desired drawdown, and NOT a risk budget to spend.
   - The strategy must operate comfortably well below this boundary at all times.
2. **`[MONITORING THRESHOLD]` Risk Review Trigger Levels:**
   - **`~15.0% Drawdown`:** **Elevated Risk Review** $\rightarrow$ Audit trade logs for market regime shifts.
   - **`~20.0% Drawdown`:** **Serious Risk Review** $\rightarrow$ Review broker execution, slippage, and pause new entries.
3. **`[STATISTICAL REFERENCE]` Empirical & Permutation Reference Benchmarks:**
   - **`~6.2%`:** Historical Maximum Drawdown observed on XAUUSD H1 longitudinal backtests (2014–2025).
   - **`~11.8%`:** Monte Carlo 95th-percentile sequence-risk reference across 10,000 permutations.
   - *Note: Exceeding 11.8% does NOT mean the strategy is broken; it is a statistical investigation threshold.*
4. **`[PORTFOLIO RISK RULE]` Portfolio Heat & Position Constraints (V2.7 Candidate):**
   - **Max Concurrent Positions:** 2 active positions.
   - **Portfolio Heat Calculation:** Portfolio Heat must be calculated strictly from the **actual potential loss to each active position's current stop level**.
   - **Critical Distinction:** Position count alone does **NOT** guarantee a 6% maximum heat (especially when pyramiding/scale-in orders are present).
   - **Validation Requirement:** Maximum portfolio heat target/limit must be formally validated after pyramiding risk mechanics are mathematically defined.
5. **`[STRATEGY RULE]` Position Sizing & Stop Loss:**
   - Sizing: Balanced Dynamic Fixed Fractional Risk = **`3.0% of Account Equity per trade`**.
   - Hard Stop Loss: $Entry \pm (2.5 \times ATR_{14})$ [Intrabar price touch].

---

## 3. USER CONSTRAINTS & OPERATING PROFILE

### 3.1 Availability Schedule (Home Desktop Only / No VPS):
- **Trading Windows (Bangkok Time UTC+7):**
  - Morning / Afternoon: `09:00 – 16:00` (Monday – Friday)
  - Evening: `17:00 – 22:00` (Monday – Friday)
- **Offline Windows (PC Turned Off):**
  - Intermission: `16:00 – 17:00`
  - Night / Overnight: `22:00 – 09:00`
  - Weekends: Saturday & Sunday (Markets closed except Crypto).
- **Zero-Backfill Rule:** Missed signals during offline windows are audited for diagnostics only (`check_overnight_missed_trades.py`). **NEVER backfill or manually chase missed signals.**

### 3.2 Capital & Account Sizing Profile:
- **Broker:** **XM Global Limited** (MetaTrader 5)
- **Account Type:** **XM Ultra Low Account** (Swap-Free on Gold, FX, and BTC).
- **Starting Account Balance:** `10,000.00 THB` (Demo Account #1301604465) / Leverage 1:1000.
- **Monthly Savings Capacity (DCA):** `1,000.00 THB / month` (~$30 USD/month).
- **Execution Lot Resolution:** Micro lots down to `0.01 lot` (with auto-compounding dynamic sizing).

---

## 4. MULTI-ASSET UNIVERSE SPECIFICATION (TOP 5 SCREENED)

All assets trade exclusively on the **1-Hour (`H1`) Timeframe**:

| Canonical Symbol | XM Broker Suffix Aliases | Asset Class | Spread (Typical) | Swap Profile | Screening Status |
|---|---|---|---|---|---|
| **`XAUUSD`** | `GOLD#`, `GOLD`, `XAUUSDm` | Spot Gold | ~2.0–3.0 pips ($0.25/oz) | **Swap-Free** | ✅ Core Asset ($PF=1.17$) |
| **`USDJPY`** | `USDJPY`, `USDJPY#`, `USDJPYm`| Forex Major | ~0.8 pips | **Swap-Free** | ✅ Top Tier ($PF=1.22$) |
| **`GBPUSD`** | `GBPUSD`, `GBPUSD#`, `GBPUSDm`| Forex Major | ~0.8 pips | **Swap-Free** | ✅ Solid Runner ($PF=1.14$) |
| **`US500`** | `US500Cash#`, `US500#`, `US500Cash`| Equity Index CFD | ~0.70 pts | Standard Swap | ✅ Top Tier ($PF=1.25$) |
| **`BTCUSD`** | `BTCUSD#`, `BTC`, `BTCUSDm` | Crypto CFD | ~$50.00 | **Swap-Free** | ✅ High Runner ($PF=1.18$) |
| *`EURUSD`* | *`EURUSD#`* | *Forex Major* | *~0.8 pips* | *Swap-Free* | ❌ **FILTERED OUT ($PF=1.02$)** |

---

## 5. FROZEN STRATEGY V2.6 SPECIFICATION (THE MATHEMATICAL CONTRACT)

```text
               [Live Closed H1 Bar T]
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Economic Viability Filter                          │
│ ► Formula: ATR(14) / Roundturn_Friction >= 5.0              │
│ ► Rule   : ENTRY-ONLY FILTER (Never closes active positions)│
└────────────────────────┬────────────────────────────────────┘
                         │ QUALIFIED
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Market Trend Regime Filter                         │
│ ► Kaufman Efficiency Ratio: ER(14) > 0.40                   │
│ ► Bullish: ER > 0.40 AND Close(T) > Close(T-14)             │
│ ► Bearish: ER > 0.40 AND Close(T) < Close(T-14)             │
└────────────────────────┬────────────────────────────────────┘
                         │ QUALIFIED
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Timing & Execution Trigger                         │
│ ► Wilder RSI(14) [60 / 50 / 40]                             │
│ ► Bullish Entry: RSI < 50 -> Crosses > 50 on Close(T)       │
│ ► Bearish Entry: RSI > 50 -> Crosses < 50 on Close(T)       │
│ ► Constraint   : Strictly 1 Trade Per Trend Cycle           │
│ ► Execution    : Order Fills at Next Bar Open(T+1)          │
└────────────────────────┬────────────────────────────────────┘
                         │ ORDER OPENED
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Dual Exit & Position Management Layer (No Fixed TP)         │
│ ► Initial Hard SL : Entry ± (2.5 × ATR14) [Intrabar touch]  │
│ ► Thesis Exit     : Long RSI < 40 / Short RSI > 60 [Close]  │
│ ► Priority        : Whichever triggers first closes trade   │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. STRATEGY V2.7 RESEARCH CANDIDATES (UNDER LAB TESTING ONLY)

*Do NOT deploy to production bot until all 5 Gates are explicitly authorized.*

1. **Gate 1: Pyramiding Sizing & Risk Rule (Case A Locked):**
   - Trigger: When Trade 1 reaches floating gain $\ge +1.5R$ (where $1.0R = 2.5 \times ATR$).
   - Action A: Move Stop Loss of Trade 1 to **Breakeven (Entry 1)** ($\text{PnL}_1 = 0.0R$).
   - Action B: Sizing $V_2 = \lfloor \frac{2}{3} V_1 / \text{step} \rfloor \times \text{step}$ (Strict `math.floor` volume floor).
   - Action C: Stop Loss of Trade 2 set at **Entry 1** (Distance $= 1.5D$).
   - Combined Reversal Loss is bounded strictly at $\le 1.0R$ ($\le 3.0\%$ Equity).

2. **Gate 2: Portfolio Heat Engine & Clean 3-Tier Collision Resolution:**
   - **Max Concurrent Positions:** $\le 2$ active positions simultaneously.
   - **Portfolio Heat Formula:** $\sum (\text{Loss to Current Stop}_i + \text{Friction Buffer}_i) / \text{Equity} \le 6.0\%$.
   - **3-Tier Deterministic Collision Resolution (ZERO Historical Performance Bias):**
     1. Primary: Highest Kaufman $ER_{14}$ at Bar $T$ (Descending).
     2. Secondary: Lowest $\text{Spread} / ATR_{14}$ Friction Ratio (Ascending).
     3. Tertiary: Canonical Alphabetical Symbol Order (`BTCUSD` < `GBPUSD` < `US500` < `USDJPY` < `XAUUSD`).

3. **Gate 3: Multi-Asset Independent Calendar Engine:**
   - Each asset operates an isolated market session clock (BTC 24/7 vs FX/Gold 24/5 vs US500 breaks).
   - Zero cross-asset candle synthesis or timestamp forward-filling.
   - Explicit Data Integrity logging: flags missing bars and rejects duplicate timestamps without synthetic repair.

4. **Gate 4: Broker Metadata & Micro-Lot Quantization Engine:**
   - Dynamic ingestion of broker metadata (`volume_min`, `volume_step`, `contract_size`, `tick_size`, `tick_value`).
   - Strict Floor Quantization: `Quantized_Volume = floor(Raw_Volume / Volume_Step) * Volume_Step`.
   - Strict Risk Floor Rule: Actual Risk $\le$ Target Risk (3.0%). If `Quantized_Volume < Volume_Min` $\implies$ **REJECT TRADE** (Never round up!).
   - Free margin safety buffer: `Free Margin >= Required Margin * 1.25`.

5. **Gate 5: Final Integrity & State Pipeline (Audited & Locked):**
   - Complete end-to-end event orchestrator [`rsi_trend_pullback/research/v27_integrity_pipeline.py`](file:///d:/Kaeha/rsi_trend_pullback/research/v27_integrity_pipeline.py).
   - Strict Pyramiding Order of Operations: Modify SL1 to BE $\rightarrow$ Verify fill $\rightarrow$ Sizing V2 $\rightarrow$ Check Heat/Margin $\rightarrow$ Open Trade 2.
   - Gap & Slippage Realism: Stops gapped through fill at candle open (never synthetic zero-loss BE).
   - Sequential collision resolution re-evaluating dynamic portfolio state after each fill.
   - 0 Critical Issues, 0 High Issues, 0 Look-Ahead Leaks across all 12 test suites.

---

## 7. STRICT PROHIBITIONS ("สิ่งที่ห้ามแก้ไขเด็ดขาด")

1. **NO Look-Ahead Bias:** Never use future price data to trigger historical orders.
2. **NO Strategy Curve-Fitting:** Do not alter RSI period (14), ER threshold (0.40), or ATR multiplier (2.5) because of individual asset performance.
3. **NO Trade Backfilling:** When starting after an offline window, never enter missed past signals.
4. **NO Fixed TP:** Preserve the unconstrained Trend Runner thesis exit.
5. **NO Martingale:** Never double lot size on losing trades.

---

## 8. CODEBASE DIRECTORY & EXECUTION MAP

```text
d:/Kaeha/
├── rsi_trend_pullback/
│   ├── mt5_multi_asset_paper_trader.py    # Master Multi-Asset MT5 Paper Trader (5 Assets)
│   ├── check_overnight_missed_trades.py   # Live 24h Overnight Missed Trade Audit Scanner
│   ├── mt5_paper_trader.py                # Single-Asset MT5 Paper Trader (XAUUSD)
│   ├── strategy/v26_strategy.py           # Frozen Strategy V2.6 Engine
│   └── tests/test_v26_implementation.py   # 8-Dimension Unit Test Suite (100% Passing)
├── run_multi_bot.bat                      # 1-Click Multi-Asset Bot Launcher (Desktop)
├── check_missed_trades.bat                # 1-Click Overnight Missed Trades Checker
├── run_bot.bat                            # 1-Click Single-Asset Bot Launcher
├── PROJECT_CONTEXT.md                     # THIS DOCUMENT (Master Single Source of Truth)
└── README.md                              # Master GitHub Documentation
```
