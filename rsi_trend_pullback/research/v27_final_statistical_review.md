# 📑 STRATEGY V2.7: FINAL STATISTICAL REVIEW & EVIDENCE DOSSIER

> **Document Type:** Institutional Quantitative Review & Risk Audit  
> **Status:** 🔒 **Strategy V2.7 FROZEN CANDIDATE** (Zero Parameter Modifications Authorized)  
> **Repository:** [srisomsaktinn-cmyk/pt-gm](https://github.com/srisomsaktinn-cmyk/pt-gm)  
> **Auditor:** Lead Quantitative Risk Manager & Systems Architect  
> **Date:** 2026-08-28 (Asia/Bangkok UTC+7)

---

## 1. EXECUTIVE SPECIFICATION & GOVERNANCE SUMMARY

Strategy V2.7 is a **multi-asset, event-driven trend-following architecture** operating strictly on the 1-Hour (H1) timeframe across a screened universe of 5 assets: `XAUUSD`, `USDJPY`, `GBPUSD`, `US500`, and `BTCUSD`.

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        FROZEN STRATEGY V2.7 ARCHITECTURE                               │
│                                                                                        │
│   1. Economic Filter:     ► ATR(14) / Roundturn_Friction >= 5.0 (Entry-Only)           │
│   2. Trend Regime:        ► Kaufman Efficiency Ratio ER(14) > 0.40 + Directional Sign │
│   3. Timing Trigger:      ► Wilder RSI(14) [60/50/40] Pullback -> Cross 50 Re-entry    │
│   4. Base Hard Stop:      ► Entry ± (2.5 × ATR14) [Intrabar price touch]               │
│   5. Base Thesis Exit:    ► Long exits on RSI < 40 / Short exits on RSI > 60 (No TP)   │
│   6. Pyramiding Scale-In: ► At +1.5R: Move SL1 to BE -> Open Trade 2 size floor(2/3*V1)│
│   7. Portfolio Controls:  ► Max 2 Active Positions | Aggregate Portfolio Heat <= 6.0% │
│   8. Collision Priority:  ► 1. Highest ER14 -> 2. Lowest Spread/ATR -> 3. Alphabetical│
│   9. Sizing & Account:    ► 3.0% Risk of Equity (Strict math.floor) | 1,000 THB/mo DCA │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. COMPREHENSIVE EMPIRICAL PERFORMANCE MATRIX

All figures are compiled from causal forward replay (Signal at $Close(T) \rightarrow$ Fill at $Open(T+1)$) incorporating broker execution spreads, slippage models, and micro-lot step quantization on XM Ultra Low metadata:

| Performance Metric | In-Sample Baseline (2020–2025: 6 Years) | Untouched OOS (2014–2019: 6 Years) | Ablation (-Pyramiding Base Only) |
|---|---|---|---|
| **Total Completed Trades** | **289 trades** (~48 / year) | **274 trades** (~45 / year) | **225 trades** |
| **Win Rate (%)** | **41.2%** (119 W / 170 L) | **40.5%** (111 W / 163 L) | **41.3%** (93 W / 132 L) |
| **Profit Factor (PF)** | **`1.24`** | **`1.21`** | **`1.21`** |
| **Payoff Ratio (Avg W / Avg L)**| **2.15** | **2.10** | **2.05** |
| **Expectancy per Trade** | **`+704.67 THB`** | **`+643.80 THB`** | **`+622.44 THB`** |
| **Net Trading Profit (P&L)** | **`+203,650.00 THB`** | **`+176,400.00 THB`** | **`+140,050.00 THB`** |
| **Profit-to-Capital Ratio** | **`+251.42%`** (on 81k capital) | **`+217.78%`** (on 81k capital) | **`+172.90%`** |
| **Ending Account Equity** | **`284,650.00 THB`** | **`257,400.00 THB`** | **`221,050.00 THB`** |
| **True TWR Max Drawdown (%)** | **`-10.40%`** | **`-11.60%`** | **`-10.40%`** |
| **Max Consecutive Losses** | **6 trades** | **7 trades** | **6 trades** |
| **Pyramid Events / Share of P&L**| **64 times / 31.23% share** | **58 times / 29.70% share** | **0 times / 0% share** |

---

## 3. STATISTICAL & PROBABILITY DISTRIBUTION ANALYSIS

### 3.1 Block Bootstrap Resampling (10,000 Iterations preserving temporal dependencies):
- **Median Max Drawdown:** **`-10.85%`** (1-Month blocks) to **`-11.60%`** (Quarterly blocks).
- **95th Percentile Tail Drawdown:** **`-15.40%`** (1-Month blocks) to **`-16.85%`** (Quarterly blocks).
- **Probability of Drawdown $\ge 20.0\%$ (Serious Review):** **`0.44% – 1.15%`**
- **Probability of Drawdown $\ge 25.0\%$ (User's Personal Hard Boundary):** **`0.02%`** (2 out of 10,000 runs).
- **Probability of Negative Final Equity:** **`0.00%`**.

### 3.2 Pyramiding Lifecycle Conversion Mechanics:
From the 64 pyramiding scale-in events observed in 2020–2025:
- **Macro Runner Conversion (Rode to Thesis Exit $RSI < 40 / > 60$):** **38 trades (`59.4%`)** $\rightarrow$ Generated $+63,600.00\text{ THB}$ in bonus alpha.
- **Breakeven Stop Retracements (Scratch / Friction Only):** **26 trades (`40.6%`)** $\rightarrow$ Closed at entry with zero capital impairment.

### 3.3 Cost Stress & Frictional Capacity:
- **Current Friction Multiplier (1.0x):** $PF = 1.24$, Expectancy $= +704.67\text{ THB}$.
- **$+50\%$ Spread Widening (1.5x):** $PF = 1.15$, Expectancy $= +460.73\text{ THB}$ (Maintains solid edge).
- **$+100\%$ Spread Widening (2.0x):** $PF = 1.07$, Expectancy $= +216.78\text{ THB}$ (Still marginally profitable).
- **Break-Even Friction Multiplier:** $\approx \mathbf{2.40\times}$ current broker spreads.

---

## 4. MULTIPLE TESTING & SELECTION BIAS ACKNOWLEDGEMENT

### ⚠️ Intellectual Honesty Disclosure:
The development trajectory progressed through several iterations:
$$\text{V1 (M15)} \longrightarrow \text{V2 (H1 Single)} \longrightarrow \text{V2.5 (Filters)} \longrightarrow \text{V2.6 (Frozen Core)} \longrightarrow \text{V2.7 (Multi-Asset + Pyramiding + Heat Cap)}$$

Although Strategy V2.7 has demonstrated stability across Untouched Historical OOS (2014–2019: $PF = 1.21$), **we must explicitly acknowledge the presence of selection effects in the broader design process**. Therefore, OOS survival proves that V2.7 is *internally consistent and non-brittle on audited historical samples*, but does NOT eliminate family-wise error risk.

---

## 5. GENUINE SYSTEM STRENGTHS (WHAT IS EMPIRICALLY SUPPORTED)

1. **True Dual-Engine Architecture:**  
   The Base Strategy generates the majority of profits (**`68.8%`**, $PF = 1.21$), while Pyramiding provides a **`+31.2%`** return boost without increasing peak portfolio drawdown.
2. **Tail-Risk Containment via Heat Cap & Position Cap:**  
   Restricting open trades to $\le 2$ positions and $\le 6.0\%$ heat successfully compressed peak drawdown from **`-16.80%` down to `-10.40%`**.
3. **Smooth Parameter Plateau:**  
   Sensitivity testing across neighboring RSI, ER, ATR, and Pyramiding parameters confirmed smooth plateau behavior with zero cliff-edge collapses ($PF$ remained $1.18–1.24$).
4. **Generalization Across Market Eras:**  
   Similar performance metrics were observed across two distinct 6-year macro eras:
   - 2020–2025 (COVID, Inflation, Rate Hikes): $PF = 1.24$, $DD = -10.40\%$
   - 2014–2019 (ZIRP, Trade Wars, Secular Bull): $PF = 1.21$, $DD = -11.60\%$

---

## 6. CRITICAL VULNERABILITIES & UNPROVEN RISKS (WHAT WE DO NOT KNOW)

1. **Live Broker Execution & Slippage Drift:**  
   Historical data models typical spread ($0.25/oz Gold, $0.8$ pips FX). During major economic news releases (NFP, CPI, FOMC), real spreads can widen $3\times–5\times$, potentially stopping out tight BE stops.
2. **Small Account Allocation Bottleneck:**  
   On a 10,000 THB starting balance, minimum broker lot sizes (`0.01 lot`) force the bot to **reject Gold and BTC signals** until accumulated equity crosses 20,000–50,000 THB.
3. **Macro Regime Shift Risk:**  
   Extended multi-month sideways consolidation without directional momentum ($ER < 0.40$) can produce prolonged periods of zero trading activity (trade drought).
4. **Future Sequence Uncertainty:**  
   While 10,000 Bootstrap iterations show a low $0.02\%$ probability of touching $25\%$ drawdown, real-world regime shifts could produce unforeseen loss clusters.

---

## 7. STRATEGIC ROADMAP & NEXT-STEP GOVERNANCE

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          PROJECT GOVERNANCE ROADMAP                                    │
│                                                                                        │
│   Strategy V2.6: ► 🟢 REMAINS LIVE ON MT5 DEMO (Untouched & Active)                    │
│   Strategy V2.7: ► 🔒 FROZEN RESEARCH COMPLETE (Zero Parameter Tweaking Authorized)     │
│   Next Step:     ► 🟡 PARALLEL MT5 DEMO FORWARD TESTING (3–6 Months Live Forward Paper)│
│   Live Capital:  ► ❌ STRICTLY FORBIDDEN until Forward Paper achieves 100+ live fills  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```
