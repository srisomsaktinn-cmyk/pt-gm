# ⚔️ ADVERSARIAL "BREAK MY BOT" TEST REPORT: STRATEGY V2.7

> **Objective:** Actively attack the V2.7 algorithmic trading implementation across 5 failure domains:
> 1. Data Attacks
> 2. Market Attacks
> 3. Broker & Sizing Attacks
> 4. State & Crash Attacks
> 5. Portfolio & Heat Attacks

---

## 1. ADVERSARIAL TEST RESULTS SUMMARY

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                   ADVERSARIAL QA ATTACK MATRIX & DEFENSE SCORECARD                     │
├────────────────────────────┬──────────────────────────────────┬──────────────┬─────────┤
│ Attack Vector Category     │ Simulated Adversarial Scenario   │ System Action│ Verdict │
├────────────────────────────┼──────────────────────────────────┼──────────────┼─────────┤
│ 1. Data Attack             │ Malformed OHLC (High < Low)      │ Ignore Bar   │ 🟢 PASS │
│ 2. Data Attack             │ +50% Flash Jump + 0 Volume       │ Zero Div Safe│ 🟢 PASS │
│ 3. Market Attack           │ 300-Pip Weekend Gap Past Stop    │ Fill at Open │ 🟢 PASS │
│ 4. Market Attack           │ 10x Spread Spike (Illiquid Open) │ Reject Entry │ 🟢 PASS │
│ 5. Broker Sizing Attack    │ Small Balance (< Min Lot Size)   │ Reject Entry │ 🟢 PASS │
│ 6. Broker Sizing Attack    │ Fractional Volume 0.0195 Lot     │ Floor 0.01   │ 🟢 PASS │
│ 7. State / Crash Attack    │ Corrupted State JSON on Startup  │ Safe Resync  │ 🟢 PASS │
│ 8. Portfolio Attack        │ 5 Assets Signal Simultaneously   │ Accept Top 2 │ 🟢 PASS │
│ 9. Portfolio Attack        │ Heat Cap Overflow (7.0% > 6.0%)  │ Reject Entry │ 🟢 PASS │
└────────────────────────────┴──────────────────────────────────┴──────────────┴─────────┘
```

---

## 2. KEY DEFENSE PROOFS

1. **3-Tier Collision Resolution Defense:** When all 5 assets signal at the exact same H1 bar, the system sorts candidates by $ER_{14}$ then $\text{Spread/ATR}$, fills the top candidate (`US500` with $ER=0.65$), immediately recalculates heat, fills the second candidate (`USDJPY` with $ER=0.55$), and strictly rejects the remaining 3 candidates because active positions reach the max cap of 2.
2. **Floor Sizing Protection:** Sizing calculations use strict `math.floor` quantization. Under no scenario does volume round upward to inflate risk beyond the 3.0% target.
3. **Gap Through Stop Realism:** If price gaps past a stop loss on market open, simulated exits fill at $Open(T+1)$ (the worse price), preventing overly optimistic fill assumptions.
