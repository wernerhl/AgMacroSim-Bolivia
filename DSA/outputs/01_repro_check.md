# 01 Reproduction gate

Question: fed the program's policy path, does the instrument return the MEFP's own deficit, debt,
growth, and inflation within tolerance? Run this before any stress; do not proceed on a failed gate.

## Result: PASS on the MEFP-anchored reduced-form core; MFMod-BOL v5 not used as the baseline generator

Two things are distinct.

1. **The reduced-form core, fed the MEFP path, reproduces the MEFP by construction and reconciles the
   cross-checks.** The core takes the cited anchors (growth minus 1.6 in 2025, primary floors from
   Cuadro 1, zero primary by 2029, debt 80 official / 90 market at end-2025) and returns the program's
   stated debt trajectory: a rise to about 87 / 89 percent in 2026 on the official-rate unification,
   then a decline below 90 percent at both valuations by 2029 (MEFP p.9, para 22). Independent
   cross-checks that were not imposed:
   - Overall deficit 2026: core returns about 8.9 percent of GDP; MEFP Cuadro 1 line 6 implies about
     9.3 percent (minus 46.8 bn on GDP about 505 bn). Within 0.4 point, the residual being the
     interest approximation.
   - Overall deficit 2029: core returns 3.5 percent of GDP; MEFP p.5 para 11 target is 3.5 percent.
   - End-2025 dual valuation: an FX share of 0.31 and a reference rate of about 9.8 reproduce the 80
     official / 90 market statement (MEFP p.8, para 21).
   These are within tolerance (deficit levels to about half a point; debt levels to the stated
   thresholds), so the gate passes.

2. **MFMod-BOL v5 does not reproduce the MEFP out of the box, and is not asked to be the baseline.**
   v5 was estimated on data through 2024 and benchmarked to the April-2025 Article IV
   (`Output/BOL_MFMod_v5_vs_IMF.csv`), before this program. Its independent call for 2025 real GDP is
   about minus 3.3 percent, against the MEFP's minus 1.6 percent; its fiscal deficits run a few points
   smaller than the program's. Per the work order, when the model fed the program assumptions does not
   reproduce the MEFP within tolerance, the baseline is recalibrated to the MEFP and the difference is
   documented. That is done here: the baseline is the MEFP path, and MFMod-BOL supplies structure (the
   debt identity blocks, the FX and price channels) and elasticities (the public-investment-to-growth
   channel used in S2 and S8), not the headline projection. The one number that moved is 2025 growth,
   from the model's minus 3.3 to the program's minus 1.6, and the fiscal path, from the model's
   independent projection to the Cuadro 1 floors.

## What this means for the reading
The DSA is reduced-form with MEFP anchors. It is not a claim that MFMod-BOL, re-estimated, would
generate the MEFP path; it is a claim that the debt-dynamics identity, fed the program's own growth,
inflation, primary, and FX assumptions, produces the program's stated debt trajectory and its
cross-checks. The distinction is carried through every headline in `IDENTIFICATION_NOTE.md`.
