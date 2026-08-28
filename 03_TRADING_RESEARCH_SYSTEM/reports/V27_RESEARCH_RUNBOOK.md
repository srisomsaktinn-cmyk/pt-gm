# 📖 STRATEGY V2.7: MASTER QUANTITATIVE RESEARCH & OPERATIONS RUNBOOK

**Target Strategy:** Strategy V2.7 Multi-Asset Pullback Engine  
**Governance Status:** 🔒 **FROZEN CANDIDATE** (Strict Observability & Forward Demo Testing)  
**Authoritative Contract:** [`PROJECT_CONTEXT.md`](file:///d:/Kaeha/PROJECT_CONTEXT.md)

---

## 1. 🚀 QUICK START & MASTER 1-CLICK LAUNCHERS

The repository provides modular, 1-click batch scripts located in `d:\Kaeha\`:

| Batch Script Name | Purpose & Execution Flow | Output Artifacts Generated |
|---|---|---|
| **`run_v27_full_research.bat`** | **Executes Complete End-to-End Research Suite** (Data audit $\rightarrow$ Unit tests $\rightarrow$ Independent validator $\rightarrow$ Adversarial harness $\rightarrow$ Analytics $\rightarrow$ Reports $\rightarrow$ HTML Dashboard) | `PROJECT_ARCHITECTURE_REPORT.md`, `adversarial_test_report.md`, `v27_full_research_dashboard.html`, `v27_research_manifest.json` |
| **`run_v27_demo_bot.bat`** | Launches Live MT5 Multi-Asset Paper Trader connected to XM Demo | `v27_paper_trading.log`, `v27_forward_trades.csv`, `v27_active_positions_state.json` |
| **`run_v27_dashboard.bat`** | Real-Time Terminal & Telemetry Dashboard | Live CLI Terminal, `v27_daily_health_report.md` |
| **`run_independent_validation.bat`** | Runs clean-room independent reference validator | `v27_independent_validation_report.md`, `v27_independent_vs_original_diff.csv` |
| **`run_v27_tail_value_analysis.bat`** | Runs Top-Winner and Tail-Loss distribution analysis | `v27_missed_tail_value_analysis.md`, `v27_missed_tail_value_analysis.csv` |
| **`run_v27_coverage_analysis.bat`** | Analyzes User Schedule (09:00-16:00 & 17:00-22:00) | `v27_personal_schedule_coverage.md`, `v27_personal_schedule_coverage.json` |

---

## 2. 🗂️ DIRECTORY & ARTIFACT REPOSITORY STRUCTURE

```text
D:\KAEHA\
├── PROJECT_CONTEXT.md                    <-- Master SSOT Governance Contract
├── PROJECT_ARCHITECTURE_REPORT.md        <-- Full System Architecture & Flow Map
├── V27_RESEARCH_RUNBOOK.md               <-- Master Operations & Execution Runbook
├── broker_metadata_snapshot.json         <-- Authoritative Broker Specification
├── independent_v27_backtest.py           <-- Clean-Room Independent Reference Validator
├── v27_independent_trades.csv            <-- Trade-by-trade independent backtest fills
├── v27_forward_trades.csv                <-- High-resolution live forward trade telemetry
├── missed_signals.csv                    <-- Offline missed signal database
├── v27_full_research_dashboard.html      <-- 16-Panel Master Interactive HTML Dashboard
├── v27_research_manifest.json            <-- Cryptographic SHA-256 Dataset & Code Manifest
│
└── rsi_trend_pullback/
    ├── data/                             <-- Raw H1 CSV market data & loader
    ├── monitoring/                       <-- Telemetry DB, reporting engine, health sentinels
    ├── analytics/                        <-- Unified data model & forensic analytics engines
    ├── research/                         <-- Sizing, heat, calendar, and stress engines
    └── tests/                            <-- Automated unit, integration, & adversarial suites
```

---

## 3. 🛡️ STRICT QUANT DISCIPLINE & FAIL-SAFE RULES

1. **Strict Data Separation Invariant:**
   * `FORWARD_EXECUTED`: Real orders placed and filled on MT5 Demo.
   * `MISSED_SIGNAL`: Signals occurring during offline hours (recorded for research only; NEVER added to Forward P&L, Win Rate, or Drawdown).
2. **True TWR Unit-NAV Accounting:**
   * Monthly DCA capital additions (81,000 THB total external capital) are strictly tracked in capital ledger and isolated from trading P&L (+203,650 THB). True Drawdown remains **`-10.40%`**.
3. **No Strategy Mutation:**
   * No parameters or indicators may be modified based on backtest or forward observations without formal, documented authorization.
