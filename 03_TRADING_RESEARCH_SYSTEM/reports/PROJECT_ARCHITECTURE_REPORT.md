# 🏛️ STRATEGY V2.7: MASTER ARCHITECTURE & DEPENDENCY REPORT
**System Component:** Comprehensive Algorithmic Trading & Quantitative Research Framework  
**Governance Status:** 🔒 **Strategy V2.6 FROZEN** | 🔒 **Strategy V2.7 FROZEN CANDIDATE**  
**Generated:** 2026-08-28 (Asia/Bangkok UTC+7)

---

## 1. HIGH-LEVEL ARCHITECTURAL TOPOLOGY

```text
                                  ┌───────────────────────────────────┐
                                  │      RAW MARKET DATA (H1 CSV)     │
                                  │ (XAUUSD, USDJPY, GBPUSD, US, BTC) │
                                  └─────────────────┬─────────────────┘
                                                    │
                                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    DATA INGESTION & CALENDAR ENGINE                                    │
│  • rsi_trend_pullback/data/loader.py (Strict Causal Candle Streaming)                                  │
│  • rsi_trend_pullback/research/multi_asset_calendar_engine.py (Independent 24/5 vs 24/7 Asset Clocks)   │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │
                                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   CORE INDICATOR & STATE MACHINE PIPELINE                              │
│  • Layer 1: Economic Filter (ATR14 / Roundturn Friction >= 5.0)                                       │
│  • Layer 2: Kaufman Efficiency Ratio (ER14 > 0.40 & Trend Direction)                                 │
│  • Layer 3: Wilder RSI(14) Pullback Timing (60/50/40 Regime Cycles)                                   │
│  • Layer 4: Hard ATR Stop Loss (2.5 x ATR14) & Thesis Exits (RSI < 40 Long / RSI > 60 Short)          │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │
                                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   PORTFOLIO, RISK & EXECUTION GATES                                    │
│  • Gate 1: 3-Tier Collision Ordering (Highest ER14 -> Lowest Spread/ATR -> Canonical Order)           │
│  • Gate 2: Sequential Portfolio Heat Sentinel (SUM(Market Loss to SL + Friction) / Equity <= 6.0%)     │
│  • Gate 3: Concurrent Position Cap (Active Positions <= 2)                                            │
│  • Gate 4: Broker Sizing Engine (3.0% Risk / Strict Floor Step Quantization / Min Lot Rejection)       │
│  • Gate 5: Pyramiding Scale-In Engine (+1.5R Trigger -> SL1 to BE -> Size 2/3 Base Volume)             │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │
                   ┌────────────────────────────────┴────────────────────────────────┐
                   ▼                                                                 ▼
┌──────────────────────────────────────┐                         ┌──────────────────────────────────────┐
│       LIVE MT5 DEMO TRADER           │                         │     INDEPENDENT CLEAN-ROOM ENGINE    │
│ • mt5_v27_paper_trader.py            │                         │ • independent_v27_backtest.py        │
│ • v27_forward_telemetry.py           │                         │ • compare_v27_independent_vs_...     │
│ • v27_forward_trades.csv             │                         │ • Zero Strategy Engine Imports       │
└──────────────────┬───────────────────┘                         └──────────────────┬───────────────────┘
                   │                                                                │
                   └────────────────────────────────┬───────────────────────────────┘
                                                    │
                                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              RESEARCH, FORENSICS & OBSERVABILITY SUPERSET                              │
│  • v27_analytics_engine.py (Unified Data Model & 20 Quantitative Analytics Dimensions)                 │
│  • v27_missed_signal_auditor.py (Offline Opportunity Detection & Complete Isolation)                   │
│  • v27_personal_coverage_analyzer.py (User Schedule 09:00-16:00 & 17:00-22:00 Coverage Study)        │
│  • v27_adversarial_harness.py (Data, Market, Broker, State, and Portfolio Attack Vectors)            │
│  • v27_full_research_dashboard.html (16-Panel Offline Interactive Dashboard)                          │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. MODULE DEPENDENCY & FLOW MATRIX

| Subsystem | Primary Python Modules | Dependent Data / Config Files | Key Invariants Enforced |
|---|---|---|---|
| **Data & Calendar** | `data/loader.py`, `multi_asset_calendar_engine.py` | `rsi_trend_pullback/data/*.csv` | Zero forward-fill, independent clocks, no look-ahead. |
| **Strategy & Logic** | `v27_integrity_pipeline.py`, `independent_v27_backtest.py` | `PROJECT_CONTEXT.md` | Wilder smoothing, strict cross definitions, 2.5x ATR stops. |
| **Risk & Portfolio** | `portfolio_heat_engine.py`, `broker_sizing_engine.py` | `broker_metadata_snapshot.json` | Heat $\le 6.0\%$, Positions $\le 2$, $\lfloor \text{Floor} \rfloor$ step sizing. |
| **Live Execution** | `mt5_v27_paper_trader.py`, `v27_forward_telemetry.py` | `MetaTrader5` API, `v27_active_positions_state.json` | Causal $Open(T+1)$ fills, BE stop ratchet before pyramid. |
| **Monitoring & QA** | `v27_daily_health_monitor.py`, `test_v27_forward_monitoring.py` | `v27_forward_trades.csv`, `v27_risk_alerts.log` | Slippage alerts ($> 3$ pips), spread spikes, latency tracking. |
| **Research & Stats** | `v27_analytics_engine.py`, `v27_missed_economic_analyzer.py` | `v27_independent_trades.csv`, `missed_signals.csv` | Strict isolation of missed signals & DCA from Trading P&L. |

---

## 3. IDENTIFIED FRAGILE AREAS & FAIL-SAFE DEFENSES

1. **Broker Slippage & Spread Spikes during Macro News:**
   - *Risk:* Sudden spread expansion causing unquantized heat spike.
   - *Defense:* Pre-trade friction buffer in Heat Engine Gate 2 + spread spike alerts at execution.
2. **PC Restart & Crash Recovery during Active Pyramiding:**
   - *Risk:* Losing track of parent trade ID or un-ratcheted BE stop.
   - *Defense:* Atomic JSON state persistence in `v27_active_positions_state.json` with multi-tier restart reconciliation.
3. **Data Contamination between Historical Backtest & Live Forward Data:**
   - *Risk:* Accidental aggregation of hypothetical missed signals with real demo equity.
   - *Defense:* `UnifiedTradeRecord` schema enforcing mutually exclusive `source_type` tags.
