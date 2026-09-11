# 06 Robustness and inference

## Stochastic fan
Growth and the effective real rate are drawn as innovations around the baseline path with the
historical joint covariance (2002 to 2024: real growth mean 3.2 percent and standard deviation 4.6;
real effective rate mean minus 2.0 percent and standard deviation 2.8; correlation about zero). One
thousand draws, seed 20260910. The primary path is held at the scenario values.

| Statistic | S0 | S7 (combined adverse) |
|---|---|---|
| Probability the ratio is on a declining path in 2029 | 73 percent | 62 percent |
| Median 2029 debt (official) | about 81 | about 87 |
| 90th percentile 2029 debt (official) | about 93 | about 99 |
| 90th percentile 2030 debt (official) | about 93 | about 100 |

The central case declines; the adverse tail does not. Under S7 the 90th percentile reaches about 97
to 100 percent through 2028 to 2030, the divergence tail, before the carry pulls it back. The
probabilities are inference around the identity, not a structural forecast.

One caveat on the fan is a property of the sample. The historical joint distribution is drawn from a
period in which the real effective rate was usually negative (financial repression, concessional
external debt, inflation). The program aims to end that regime (single-digit inflation, market-based
rates). To that extent the historical fan is favorable relative to a post-program world, and the true
tail under successful disinflation is fatter than the 27 to 38 percent read here. The bifurcation
analysis in `05_bifurcation.md` addresses that world directly rather than through the historical fan.

## Sensitivity panels
On the parameters the result rides on (2029 debt, official valuation, from `data/analysis.json`):

- **Post-2028 growth**: 0 percent gives 84 (93 market); 1 percent gives 82 (91 market); 2 percent
  gives 81 (89 market); 2.75 percent gives 80 (88 market); 3.5 percent gives 78 (87 market). The
  market-rate 90 line is the binding constraint and it is crossed near 1.7 percent growth.
- **Public-investment elasticity of potential growth**: carried through the S2 versus S8 gap, about 2
  to 4 points of the debt ratio by 2035 for a full swing from capex-heavy to capex-protected cuts.
- **FX share and depreciation size (the sfa_FX channel)**: with no further depreciation, 2029 debt is
  81 at share 0.31 and 82 at share 0.40; a 25-percent second depreciation in 2027 raises it to 86 at
  share 0.31 and 89 at share 0.40. The stock revaluation is material for the level but partly
  self-corrects because depreciation feeds inflation and deepens the negative carry.
- **Contingent-liability size**: 5 percent of GDP gives 85; 7.5 percent gives 88; 10 percent gives
  90.1. This is the one stock shock with no offsetting flow channel, and the only parameter that puts
  the baseline above 90 at the official valuation on its own.

## Dual reporting
Every headline is reported at the official peg valuation and the market valuation, with the full
street-parallel valuation carried as the adverse bound (end-2025 stock on the order of 100 to 105
percent). The GDP rebase splice is used for the historical ratios and the fan distribution; the
unspliced series raises the pre-2017 growth base and lowers estimated historical growth by about half
a point on average, which widens the fan's lower tail marginally and does not change the sign of any
headline. The analysis is annual; no high-frequency inference is drawn.
