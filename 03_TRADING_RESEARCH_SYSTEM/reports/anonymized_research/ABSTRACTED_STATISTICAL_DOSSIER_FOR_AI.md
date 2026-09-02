# 📊 ABSTRACTED QUANTITATIVE STRATEGY STATISTICAL DOSSIER
**Mode:** Blind Zero-Lookahead Audit (Anonymized Multi-Asset H1 Trend System)
**Universe:** 5 Anonymized Continuous Hourly Series (SERIES_001 to SERIES_005)

---

## 1. Pooled Execution Metrics (Raw 289-Trade Blended Log)
- **Total Trades:** 289 closed executions (225 Base entries + 64 Pyramid scale-in legs)
- **Win Rate:** 41.52% (120 Wins / 169 Losses)
- **Profit Factor (Pooled $\Sigma \text{Wins} / \Sigma |\text{Losses}|$):** 1.232
- **Payoff Ratio (Avg Win / Avg Loss):** 1.74x
- **Expectancy per Trade:** +704.67 Base Currency Units (~0.23R)
- **Max Closed Consecutive Losses:** 7 trades
- **Max Account Drawdown:** 10.40%

---

## 2. Per-Series Anonymized Performance Distribution
| Anonymized ID | Share of Trades | Series Win Rate | Series PF | Implied Payoff Ratio |
|---|---|---|---|---|
| **SERIES_001** | 22.1% (64 trades) | 43.7% | 1.17 | 1.51x |
| **SERIES_002** | 20.4% (59 trades) | 46.4% | 1.22 | 1.41x |
| **SERIES_003** | 19.0% (55 trades) | 44.0% | 1.14 | 1.45x |
| **SERIES_004** | 18.3% (53 trades) | 47.1% | 1.25 | 1.40x |
| **SERIES_005** | 20.2% (58 trades) | 42.7% | 1.18 | 1.58x |

---

## 3. MFE / Giveback Distribution on Winning Trades
- **Mean Peak Excursion ($R_{peak}$):** 2.65R
- **Mean Terminal Realized Return:** 1.74R
- **Average Giveback Fraction ($g$):** 34.3%
- **MFE Giveback Percentiles:**
  - $P_{10}$ (Tightest exit): 12.5% giveback
  - $P_{25}$: 21.0% giveback
  - $P_{50}$ (Median): 33.2% giveback
  - $P_{75}$: 46.8% giveback
  - $P_{90}$ (Severe retracement): 68.4% giveback

---

## 4. Current Risk & Portfolio Architecture
- **Base Risk per Trade:** 3.0% (Quarter-Kelly mathematically calibrated)
- **Aggregate Portfolio Heat Cap:** $\le 6.0\%$
- **Economic Cluster Sub-Cap:** $\le 4.0\%$ (Max 4% risk on correlated macro cluster)
- **Max Concurrent Positions:** $\le 2$ active positions
- **Pyramid Scale-In Trigger:** $+1.5R$ with mandatory Stop Loss move to Breakeven (+costs)
- **Pyramid Volume:** $\text{floor}(\frac{2}{3} \times V_1)$
- **Initial Stop Loss:** Fixed at Entry $\pm 2.5\times\text{ATR}_{14}$
