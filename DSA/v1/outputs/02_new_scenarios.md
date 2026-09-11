# 02 Feasible new scenarios

These extend the completed DSA. The reduced-form core in `MFMOD_BOL/DSA/outputs/02_dsa_core.md` is
reused unchanged; only the growth, interest, or stock-flow inputs move, and each change is stated. All
are illustrative structured scenarios, not forecasts. Debt is reported at the official and the market
valuation (percent of GDP). Exhibit: `exhibits/fig_scenarios.png`.

## S9: ISAE near-term baseline
Construction: replace 2026 baseline growth with the ISAE central read (minus 2.8), and run the band on
the fire-adjusted upper (minus 1.4) and the decree lower (minus 6). The 2028-and-after recovery stays
MEFP-based, flagged, because the ISAE has no signal there.

| Path | 2027 | 2028 | 2029 | 2031 | 2035 |
|---|---|---|---|---|---|
| S0 baseline | 85/87 | 83/85 | 81/82 | 77/78 | 70/72 |
| S9 upper (minus 1.4) | 86/88 | 84/85 | 81/83 | 77/79 | 71/72 |
| S9 central (minus 2.8) | 87/89 | 84/86 | 82/84 | 78/80 | 72/73 |
| S9 lower (minus 6.0) | 89/91 | 87/89 | 84/86 | 80/82 | 74/75 |

Reading: the deeper near-term contraction shifts the debt path up by about 1 to 2 points and erodes
the cushion to the 90 line. The market-rate 2029 ratio moves from 82 (S0) to 84 (S9 central), so the
headroom below 90 falls from about 7.6 to about 6.3 points. Even the decree lower bound holds the
2029 market-rate ratio at about 86, below 90, so the near-term downside alone does not breach the
program's stated path; it consumes most of the cushion and leaves the recovery assumption carrying the
rest. This is the independent-growth alternative baseline the DSA review requested.

## S10: disinflation-repricing success case
Construction: the program succeeds. Inflation reaches single digits by 2028 (MEFP p.10), and the
effective interest rate converges toward the market marginal rate as the concessional peg-era stock
rolls off at the 20-to-25-percent-of-GDP gross financing need (about a fifth to a quarter of the stock
reprices each year). The effective nominal rate is lifted from about 3 percent in 2026 toward about
8.5 to 9 percent by 2029 to 2031; inflation follows the baseline single-digit path. r minus g rises
toward positive.

| Year | r minus g | stabilizing primary pb* | debt official/market |
|---|---|---|---|
| 2028 | negative | negative | 86/88 |
| 2029 | about minus 0.7 | about minus 0.3 | 86/88 |
| 2030 | turns positive | about +0.6 | stops falling |
| 2031 | about +1.3 | about +0.95 | 88/90 |
| 2035 | positive | positive | 94/96 |

Reading: r minus g turns positive in 2030. From that year the programmed zero primary balance no
longer holds the ratio down: the debt path stops falling and rises to about 88/90 by 2031 and about
94/96 by 2035. The condition for renewed decline is a primary surplus of about 0.95 percent of GDP.
This is the scenario the existing set excludes by construction (S1 to S8 hold the inflation-erosion
channel roughly fixed), and it is the one the DSA findings memo identifies as the real risk: program
success removes the negative carry that was doing the deleveraging.

## S6 right-sized: contingent liabilities from the actual stock
The original S6 used an illustrative 7.5 percent of GDP. The right-sized figure is built from the
known components, at the official valuation:

| Component | Share of GDP | Basis |
|---|---|---|
| YPFB arrears to fuel traders | about 2.0 | about USD 1 billion (Section 1); MEFP fuel-supply and arrears language (p.6-7) |
| Residual arrears and payables (deuda flotante) | about 0.9 | MEFP p.5, para 11 (0.9 percent added to financing 2026-28) |
| SOE operating losses (754-entity universe) | about 1 to 3 | entity universe in `analysis/entidades_publicas_bolivia.csv`; per-entity income statements pending (v2) |
| CPVIS wind-down (BCB) | about 1 to 3 | MEFP p.3 footnote 1 and p.11, para 27 (CPVIS II, III, Fondo CPRO) |
| Gestora public-sector exposure (near-term crystallization) | about 0 to 3 | MEFP p.13, para 32 (pension-fund exposure to the public sector) |
| Bundle | low 4, central 7, high 12 | |

Restated S6 against the 90 line (debt official/market):

| Crystallization | 2027 | 2028 | 2029 |
|---|---|---|---|
| low, 4 percent of GDP | 88/89 | 87/89 | 84/86 |
| central, 7 percent | 89/91 | 90/92 | 87/89 |
| high, 12 percent | 92/94 | 95/97 | 92/94 |

Reading: at the low bundle the ratio stays below 90 at the official valuation and touches it at market.
At the central 7 percent it breaches 90 at both valuations in 2028 (90/92) before the carry pulls it
back. At the high 12 percent it reaches about 95/97 in 2028 and holds at or above 90 through 2029. This
is the single shock that breaches the 90 line on its own, and its central estimate does so. The
baseline's headroom to 90 is therefore contingent on the public-sector liability stock staying below
about 4 to 5 percent of GDP of near-term crystallization, which the available files cannot yet confirm
or deny; the per-entity SOE financials, the CPVIS schedule, and the Gestora actuarial gap are the v2
inputs that would replace the range with a point (`04_v1_to_v2.md`).
