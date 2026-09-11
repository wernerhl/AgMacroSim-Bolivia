# IMF vs MFMod-BOL — Diagnostic of Divergence

Sources checked:
- **IMF CR 25/116** (June 2025) — Bolivia 2025 Article IV consultation, concluded April 16 2025. Text Table 3 "Baseline Economic Outlook" pp.10.
- **IMF CR 25/34** (January 2025) — Bolivia 2024 Article IV.
- **IMF WEO (October 2025 vintage)** via datamapper API — more recent, more pessimistic.
- **IMF Executive Board Press Release PR 25/168** (May 30 2025).

## Side-by-side (GDP-ratio metrics)

| Indicator | Year | MFMod-BOL | IMF Art IV (Apr '25) | IMF WEO (Oct '25) |
|---|---:|---:|---:|---:|
| Real GDP growth % | 2024 | −1.1 (WDI) | **+1.3** (authorities) | −1.1 |
|  | 2025 | −5.9 | **+1.1** | −1.2 |
|  | 2026 | +0.2 | **+0.9** | −3.3 |
|  | 2027 | +0.9 | **+0.6** | n/a |
| CPI inflation (avg %) | 2025 | **3.3** | **15.1** | 19.5 |
|  | 2026 | **2.5** | **15.8** | 20.7 |
|  | 2027 | 2.4 | 17.1 | n/a |
| Fiscal balance % GDP | 2025 | −8.7 | −12.7 | −11.6 |
|  | 2026 | −8.7 | −13.2 | −9.3 |
| NFPS debt % GDP | 2024 | 85.0 (gen gov) | **95.0 (NFPS)** | 83.2 |
|  | 2025 | 96.2 | 90.4 | 84.8 |
|  | 2026 | 102.4 | 91.4 | 102.7 |
| Current acc % GDP | 2025 | −0.4 | −2.6 | −1.9 |
|  | 2026 | −0.5 | −3.2 | +1.2 |
| Nom GDP USDbn | 2025 | 53.3 | 56.3 | 64.3 |
|  | 2026 | 54.7 | 65.9 | 80.7 |

The IMF Article IV (April 2025) is the reference document. WEO Oct '25 is more recent but not yet reconciled with authorities.

## What the IMF is doing that I'm not

1. **Monetary financing channel → inflation even under the peg.** The BCB has been monetising the primary deficit (central-bank operations issuing ~5% of GDP in securities; direct financing of government). IMF para 19–20 shows domestic financing of 10.5→17.7% of GDP in 2024–2028, mostly from the central bank. This liquidity injection drives CPI to 15–17% **with the official peg held**. My Phillips curve has no fiscal-dominance channel — only an output-gap term — so my inflation prints flat.

2. **Bigger, drifting fiscal deficit.** IMF projects primary NFPS deficit −9.5% (2025) widening further because fuel subsidies balloon as parallel FX bites (direct subsidy cost 3.9% of GDP in 2024, +2.6pp of GDP if the peg devalues — Box 1 p.16). I froze revenue/expenditure at 2024 ratios, so my deficit is flat at −8.7%.

3. **NFPS perimeter.** IMF reports non-financial public sector debt including SOEs (YPFB, ENDE, COMIBOL). General-government-only debt is ~7pp lower. My 85% for 2024 is the general-gov concept — IMF's 95% is the comparable NFPS aggregate.

4. **2024 realized growth.** IMF uses BCB/INE authorities' data (+1.3% for full-year 2024, +2.1% for 9M). My WDI pull had a preliminary −1.1%. This is a data-vintage issue, and WDI will likely revise up.

5. **Authorities' data for 2024Q3 unemployment**: 3.6% — I got 3.3%, close.

6. **Unidentified financing gap.** Staff flags USD 0.8–2.1bn annual external financing gap 2025-26 → growing to USD 6bn by 2030 (Text Table 3, last rows). This is the "what gives?" line. My model implicitly closes this via residual domestic debt issuance, which is what has happened historically.

## What the IMF might be over- or mis-modeling

1. **Linear inflation creep to 20%+ forever (2030: 20.9%)** is mechanically driven by continued monetization at the current rate — there is no non-linear regime break. In reality once inflation passes ~15% there is typically a policy response (the Nov-2025 new administration, or a forced devaluation). So IMF's end-decade 20% may be a "no-policy-change" artifact.

2. **Peg held in baseline** (explicitly stated p.10: "exchange rate is assumed unchanged"). Their alternative scenario Annex III has the devaluation. So the baseline debt trajectory is artificially flat (90.4→91.4% of GDP) because the 55% external debt isn't revalued.

3. **Growth grinds to 0.2% by 2029–30** — structurally pessimistic, assumes no reform and no gas price rebound. But it is a "current policies" scenario, not a forecast.

4. **Current account widens to −4.7%** contradicts the WEO Oct vintage (+1.2% in 2026). WEO assumes import compression from FX scarcity; Art IV baseline assumes goods keep flowing. Inconsistent across IMF vintages — the reality probably splits the difference.

## What I'm doing wrong

1. **Phillips-curve-only CPI.** Need a monetary / fiscal-dominance channel. Add: `Δ log P_c = ... + φ · (M2_growth − inflation_target)` or equivalently `... + ψ · (primary_deficit_financed_by_BCB / GDP)`.

2. **Investment ECM drift.** Estimated α = −0.15 on `NEGDIFPRVKN` pulls the equation toward indefinite contraction. Either add a trend correction or impose α=0 (per WPS8965 long-run balanced-growth assumption).

3. **Fiscal block too static.** Revenue should decline with hydrocarbon-revenue erosion; expenditure should include an explicit fuel-subsidy cost that scales with parallel-FX pressure. Using WDI fiscal + BolBudget 2017-24 gives only 7–8 obs post-2010 → the ECMs are weak.

4. **Export block** with hardcoded −3%/yr gas decline is too rigid. IMF Table 3: natural gas exports 4.5% of GDP (2023) → 3.3% (2024) → 1.8% (2026) → ~0 by 2030 is the underlying gas trajectory — that's closer to −15%/yr in volume terms.

5. **WDI 2024 preliminary vintage** — should splice in BCB/INE nowcast.

6. **NFPS vs GG perimeter** — my debt ratio started at general-gov (85%) instead of NFPS (95%). A 10pp level shift.

## Honest scorecard (closer to reality, lower score wins)

| Variable | MFMod-BOL error vs Art IV (2026) | Direction |
|---|---:|---|
| Real GDP growth | −0.7pp | too pessimistic |
| **CPI inflation** | **−13.3pp** | **badly too low** |
| Fiscal balance | +4.5pp | too tight |
| Debt/GDP | +11pp | too high (but right end-state) |
| CA balance | +2.7pp | too optimistic |

The inflation miss is the big one. It's an architectural hole (no monetary-financing channel), not a coefficient issue.

## Next scenario to run

Add a monetary-financing channel and a fuel-subsidy block, keep the peg. One-liner addition to the CPI equation:

```
pi_t = 0.5*pi_{t-1} + 0.5*pi_target + 0.15*gap + 0.8*(M2_g - pi_target)
```

where M2 growth is pinned to (primary_deficit / GDP) / (1 − external_financing_share). Then re-solve.

See [05b_solve_with_monetary_financing.py](../Build/05b_solve_with_monetary_financing.py) (next step).
