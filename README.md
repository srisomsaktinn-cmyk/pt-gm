# 🏛️ KAEHA WORKSPACE: DOMAIN ARCHITECTURE & DIRECTORY MAP

This workspace is organized according to **Domain-Driven Software Architecture** into 3 distinct functional systems:

---

## 📁 DOMAIN DIRECTORIES

### 1. 🏢 `01_PEA_SAFETY_TALK_AUTOMATION/`
- **Domain:** Enterprise Document Automation & Data Processing
- **Contents:**
  - `scripts/`: Python scripts for participant parsing, office categorization, and Word docx population.
  - `input_data/`: Excel files (`Participant.xlsx`), XML tables, and markdown rosters.
  - `output_docs/`: Generated PEA Safety Talk (Cybersecurity) `.docx` meeting files.
  - `analysis_logs/`: Text log dumps and branch breakdown reports.

---

### 2. 🌐 `02_WEB_APPLICATION/`
- **Domain:** Frontend Web Application
- **Tech Stack:** React, Vite, TailwindCSS
- **Contents:**
  - `src/`: React source code, components, styles
  - `public/` & `dist/`: Web assets and distribution build
  - `package.json` & `vite.config.js`: Web project configuration

---

### 3. 📈 `03_TRADING_RESEARCH_SYSTEM/`
- **Domain:** Quantitative Algorithmic Trading & Statistical Research
- **Status:** 🔒 **Strategy V2.6 FROZEN** | 🔒 **Strategy V2.7 FROZEN CANDIDATE**
- **Contents:**
  - `rsi_trend_pullback/`: Core Python strategy, monitoring, analytics, and research package.
  - `reports/`: Master quantitative research reports (.md) and HTML dashboards.
  - `data_telemetry/`: Forward trade database CSVs, broker snapshots, and missed signal logs.
  - `runners/`: Python entry-point execution scripts.
  - `launchers/`: Modular 1-click batch files.

---

## 🚀 ROOT MASTER LAUNCHERS (1-CLICK QUICK START)

For maximum convenience, the primary operational batch files remain accessible directly in the root folder:

| 1-Click Launcher | Description |
|---|---|
| **`run_v27_demo_bot.bat`** | Launches Strategy V2.7 Live Multi-Asset Paper Trader on MT5 Demo |
| **`run_v27_dashboard.bat`** | Opens Real-Time Live Terminal Telemetry & Risk Dashboard |
| **`run_v27_full_research.bat`** | Executes the entire end-to-end Quantitative Research Pipeline |
| **`run_independent_validation.bat`** | Runs clean-room independent reference validator |
| **`PROJECT_CONTEXT.md`** | Authoritative Master Contract (SSOT) |
| **`V27_RESEARCH_RUNBOOK.md`** | Master Operations & Research Runbook |
