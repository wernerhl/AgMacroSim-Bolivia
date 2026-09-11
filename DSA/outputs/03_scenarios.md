# 03 Scenario set

S0 is the MEFP baseline. S1 to S8 are structured stresses, not forecasts; each isolates one
assumption. Magnitudes are the starting values in the work order's Appendix C and are carried as
parameters in the sensitivity grids (`06_robustness.md`). Debt levels below are official / market
valuation, percent of GDP; full table in `exhibits/tab_debt_paths.md`.

| Scenario | Construction | 2027 | 2029 | 2035 | Reading |
|---|---|---|---|---|---|
| **S0** baseline | MEFP path | 85/87 | 81/82 | 71/72 | converges below 90 by 2029 at both rates |
| **S1** growth shortfall | 2027 trough 1.5 pt deeper, 2028-29 rebound halved | 87/89 | 83/85 | 73/75 | declines less; the central test, and it does not diverge because r−g stays negative |
| **S2** investment compression | 60 percent of the cut on capex, potential growth lowered | 85/87 | 82/83 | 72/74 | the self-defeating margin: about 1 to 2 points higher than S0 by 2035 |
| **S3** reform reversal | fuel cost-recovery at 50 percent, unrest costs 0.5 pt growth, primary misses | 87/89 | 83/85 | 73/74 | political-economy fragility of the primary path; modest debt effect |
| **S4** external downside | terms of trade minus 10, oil plus 20, disbursement slip, external rate plus 150 bp | 89/91 | 87/89 | 83/85 | the r-side bites: ratio holds near 87 to 89 and barely declines; a financing gap opens on the disbursement slip |
| **S5** second FX adjustment | further 17.5 percent real depreciation in 2027, added inflation | 87/88 | 80/82 | 70/72 | the depreciation revalues FX debt through sfa_FX (a one-time stock jump) but the added inflation deepens the negative carry, so the medium-term path is close to S0 |
| **S6** contingent liabilities | 7.5 percent of GDP crystallized 2027-28 (SOEs, CPVIS, Gestora, arrears) | 89/91 | 88/89 | 77/78 | pushes the stock back above 90 (market) in 2028, then the carry pulls it down |
| **S7** combined adverse | S1 plus S2 plus S3 | 88/90 | 87/89 | 77/79 | the realistic pessimistic bundle; the ratio holds near 87 to 89 through 2029 and declines slowly, staying at or above the 90 market line for years |
| **S8** growth-protective | same envelope, cut current not capex, ring-fenced capex, concessional finance, higher potential growth from 2028 | 85/87 | 80/81 | 69/70 | the best path; about 2 to 4 points below S0 and S2 by 2035, the value of protecting investment |

## What the set shows
- No scenario diverges outright on the central parameters. The negative carry (r minus g below zero)
  is strong enough that even the combined-adverse S7 shows a slow decline rather than an explosive
  path. Divergence appears only when the carry is removed (the disinflation-plus-repricing case in
  `05_bifurcation.md` and `FINDINGS_MEMO.md` Part 3), which is not one of S1 to S8 because those hold
  the inflation-erosion channel roughly fixed.
- The stresses that keep the ratio at or above the 90 market line through 2029 are the r-side and
  stock-side ones: S4 (external rate), S6 (contingent liabilities), and the combined S7. The growth
  and reform stresses (S1, S2, S3) slow the decline but keep it below 90 at the official valuation.
- S5 is the instructive case: a second depreciation is a one-time upward revaluation of the FX stock,
  but because it also raises inflation it deepens the negative carry, so the medium-term level ends
  close to the baseline. The depreciation channel hurts the stock once and helps the flow after, a
  point that matters for reading any single depreciation year in isolation.
- The gap between S2 (cut investment) and S8 (protect investment) is the composition result: about 2
  to 4 points of the debt ratio by 2035, priced in `05_bifurcation.md`.

S1 to S8 are illustrative structured stresses. They are not forecasts and carry no probability except
through the stochastic fan in `06_robustness.md`.
