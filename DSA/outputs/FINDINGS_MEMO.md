# FINDINGS: is the program's fiscal path sustainable without growth?

A debt-sustainability analysis of the IMF (MEFP) program for Bolivia, run on the MFMod-BOL fiscal
database with a reduced-form debt-dynamics core (identity in `outputs/02_dsa_core.md`). Baseline
anchors are page-cited to the MEFP (`outputs/01_baseline.md`). Every ratio is reported at the
official peg valuation and at the market valuation. Scenarios S1 to S8 are structured stresses, not
forecasts. The debt paths are reduced-form; the growth and inflation trajectories that feed them are
MEFP-anchored where cited and program-consistent otherwise (`outputs/IDENTIFICATION_NOTE.md`).

The answer has three parts.

## Part 1: on the program's own assumptions, the ratio converges, and by a clear margin

The SPNF debt ratio falls from 80 percent (official) / 90 percent (market) at end-2025 to about 81
percent (official) / 82 percent (market) by 2029, and continues down to about 71 / 72 percent by 2035
(S0, `exhibits/tab_debt_paths.md`). It rises first, to about 87 / 89 percent in 2026, the mechanical
effect of the official-rate unification revaluing the roughly 31 percent foreign-currency share of
the stock (MEFP p.3, para 7). This meets the program's stated below-90-percent-by-2029 trajectory
(MEFP p.9, para 22) at both valuations. At the full street parallel rate (about 13.5 Bs/USD, versus
6.96 at the peg and about 9.8 at the transition reference rate), the end-2025 stock is on the order
of 100 to 105 percent, and this adverse valuation is the one to carry when judging external-servicing
capacity.

The convergence does not require a primary surplus. The stabilizing primary balance pb\* is negative
from 2027 onward, from about minus 4.8 percent of GDP in 2027 to minus 1.4 percent by 2035
(`exhibits/tab_rminusg.md`). The programmed zero primary balance from 2029 (MEFP p.5, para 11) is
therefore tighter than stabilization requires; the ratio falls even though the deficit is only closed
to zero, not pushed into surplus. The single year in which stabilization needs a small surplus
(pb\* = +0.2 percent) is 2026, and that is the one-off revaluation year, not a persisting condition.

The reason the ratio falls is not the fiscal effort. It is that r minus g is negative throughout,
from about minus 8.6 percent in 2026 to about minus 2.5 percent by 2030 (`exhibits/tab_rminusg.md`).
Bolivia's effective interest rate on the debt is low (about 2.6 percent nominal in 2024, concessional
external plus a repressed domestic market), so a real effective rate that is negative while inflation
is high erodes the local-currency two-thirds of the stock faster than the modest deficits and the FX
revaluation add to it. This is the historical norm: the real effective rate averaged minus 2.0
percent over 2002 to 2024, and real growth averaged plus 3.2 percent, a mean r minus g of about minus
5 percent (`outputs/06_robustness.md`). The primary adjustment (about 8.5 percent of GDP over
2026-29, MEFP p.5, para 11) stops the deficit from adding to the stock; the decline itself comes from
the negative carry.

## Part 2: the single assumption that flips it is growth, and the margin is thin

Given the programmed primary path, the minimum sustained post-2028 growth that keeps the market-rate
ratio below 90 percent by 2029 is 1.7 percent (`outputs/05_bifurcation.md`). The program assumes a
recovery to about 2.5 to 3 percent by 2029 (MEFP p.3, para 7, qualitative; the numeric path is
program-consistent). The cushion is therefore about 1 percentage point. Below 1.7 percent sustained
growth the market-rate ratio stays above 90 percent in 2029, breaching the program's own stated path,
though it still declines slowly rather than diverging, because r minus g stays negative.

The bifurcation surface (`outputs/05_bifurcation.md`) turns on two assumptions: post-2028 growth and
the composition of the consolidation (the share falling on capital spending). Cutting capital rather
than current spending lowers potential growth and shifts the frontier adversely: the growth-protective
S8 reaches about 80 / 81 percent by 2029 and 69 / 70 by 2035, while the investment-compression S2
reaches 82 / 83 and 72 / 74. The gap between protecting and cutting investment is about 2 to 4
percentage points of the debt ratio by 2035, the price of hitting the primary target with the
spending that raises g.

The stochastic fan (1,000 draws, seed 20260910, shocks around the baseline with the historical growth
and rate covariance) puts the probability that the ratio is on a declining path in 2029 at 73 percent
under S0 and 62 percent under the combined-adverse S7 (`outputs/06_robustness.md`). The 90th
percentile of the fan stays between 92 and 94 percent through 2029, so the adverse tail keeps the
ratio above the 90-percent line for years at the official valuation, and higher at the market
valuation. The result is convergence in the central case with a one-in-four to one-in-three tail in
which it is not.

## Part 3: what the program would need if growth disappoints, stated as bounds

If growth alone disappoints while inflation stays high, no primary surplus is required: r minus g
stays negative and even a primary deficit stabilizes the ratio (Part 1). The ratio simply declines
more slowly, or holds near 87 to 89 percent (market) as in S4 and S7.

The condition that would require a primary surplus is the removal of the negative carry, which is
what program success produces. The program targets single-digit inflation by 2028 (MEFP p.10, para
24), and the newly issued external bond (USD 1 billion, MEFP p.2, para 5) plus local-currency
issuance reprice the effective rate upward. If disinflation and repricing turn r minus g positive, to
about plus 1 percent, the stabilizing primary balance turns to about a plus 0.9 percent of GDP
surplus on an 85-percent stock, and the programmed zero primary no longer holds the ratio down. So
the sharp version of the sustainability question is not growth in isolation; it is the joint event of
successful disinflation and rate normalization (which the program intends) together with a growth
shortfall (which the program risks). In that joint state the program needs one of: a primary surplus
of the order of 1 percent of GDP, or protected investment to lift g above the 1.7-percent threshold,
or additional concessional external financing to carry the gross financing need.

Gross financing needs are the binding near-term constraint even where solvency is favorable. GFN runs
at about 24 to 25 percent of GDP in 2026 to 2027 and settles near 20 percent thereafter
(`exhibits/tab_gfn.md`), driven by domestic rollover and amortization rather than the deficit. This
is a liquidity profile, not a solvency profile: the economy is solvent on the negative carry but
exposed on the roll, which is why the external disbursements, the reserve floors (MEFP Cuadro 1,
p.17), and the liability-management swap of external for local-currency debt (MEFP p.9, para 22) are
load-bearing for the program even though the stock trajectory declines.

## One-line answer

On the program's own assumptions the debt path is sustainable and converges below 90 percent by 2029
at both exchange-rate valuations, but it converges on a negative real carry that the program's own
disinflation is designed to remove, not on the fiscal effort; the margin is a growth cushion of about
one percentage point and a gross-financing profile near 20 to 25 percent of GDP, and the path needs a
primary surplus of about 1 percent of GDP only in the joint state where disinflation succeeds, rates
normalize, and growth still disappoints.
