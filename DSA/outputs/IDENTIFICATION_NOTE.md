# IDENTIFICATION NOTE

For every headline: whether it is model-reproduced, reduced-form, or illustrative; the calibration
vintage; the parallel-rate and rebase caveats; and the annual-only limitation.

## Provenance of each headline
| Headline | Status |
|---|---|
| Baseline growth minus 1.6 (2025), inflation 14 (end-2026), primary floors, zero primary by 2029, overall to 3.5 by 2029, debt 80/90 end-2025 | **MEFP-cited** (page references in `01_baseline.md`) |
| Baseline growth 2026-2035 path, inflation 2027-2035 path, primary glide 2027-2028 | **Program-consistent** with the cited qualitative path; not MEFP figures |
| Effective interest-rate path (2.6 percent rising to 5), FX share 0.31, unification step 6.96 to 9.8, amortization shares | **Reduced-form** calibration from `analysis/` and the MEFP text |
| Debt paths S0-S8, r minus g, g\*, pb\*, GFN | **Reduced-form** debt-dynamics identity (`02_dsa_core.md`) |
| Convergence below 90 by 2029; no surplus required on baseline; minimum growth 1.7 percent; composition frontier | **Reduced-form** results of the identity |
| S1 to S8 magnitudes and paths | **Illustrative** structured stresses, not forecasts |
| Probability declining 73 / 62 percent; fan bands | **Reduced-form** inference around the identity with the historical joint distribution; not a structural forecast |
| MFMod-BOL v5 call of minus 3.3 percent 2025 growth | **Model-produced** (v5, independent), shown for the reproduction contrast; not used in the baseline |
| Distributional overlay (poverty, deciles) | **Pending**; direction stated, magnitude delegated to the companion fuel-incidence work order |

## MFMod-BOL calibration vintage
v5, April 2026 (`MFMOD_BOL/MODEL.md`, `Rawdata/bol_coefficients_v5.json`). ECM sample 2000 to 2023;
data through 2024; benchmarked to the April-2025 Article IV. It predates this MEFP. Used here for
structure and elasticities and for the reproduction contrast, not as the baseline generator
(`01_repro_check.md`).

## Parallel-rate caveat
Every debt and financing ratio appears at the official peg valuation (6.96 Bs/USD) and at the market
valuation (reference rate about 9.8, which reconciles the MEFP's 90-percent end-2025 figure). The full
street parallel rate (about 13.5, the central of the stated 1.7 to 2.2 times overstatement of USD-GDP
at the peg) is carried as the adverse bound, putting the end-2025 stock on the order of 100 to 105
percent. A single-rate figure is not treated as a result. After the mid-2026 unification the official
and market valuations converge; the meaningful dual reporting is the end-2025 gap and the
full-parallel bound.

## Rebase caveat
The 2016/17 GDP rebase breaks any ratio-to-GDP series (the 2016 level rises from 234.5 to 288.9 billion
Bs). The spliced series is used for historical ratios and the fan distribution. The unspliced series
lowers estimated historical growth by about half a point on average and does not change the sign of any
headline.

## Annual-only limitation
The data are annual and so is the DSA. No quarterly or higher-frequency inference is drawn, including
from the Cuadro 1 test points, which are read as within-year year-to-date flows (MEFP p.17, note 1),
not as an intra-year path.

## Neutral properties, not disclaimers
The reduced-form status is a property of the instrument used, chosen because the debt question is an
identity question and the model that would generate the flows predates the program. The pending
microsimulation is a scope boundary of this pass. The parallel-rate and rebase dual reporting are
features of the data. None of these changes the sign or the order of magnitude of the headline result.
