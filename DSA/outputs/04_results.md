# 04 Results per scenario, with the distributional overlay

## Exhibits produced
- `exhibits/tab_debt_paths.md` and `.tex`: debt to GDP 2026-2035 for every scenario, at the official
  and market valuation.
- `exhibits/fig_debt_fan.png`: the S0 baseline with the stochastic fan (10-90 and 25-75 bands, median)
  and the S1, S7, S8 paths overlaid, with the 90-percent line marked.
- `exhibits/tab_rminusg.md`: r minus g by year and scenario, with the stabilizing growth and the
  stabilizing primary balance and their gaps against the programmed values.
- `exhibits/tab_gfn.md`: gross financing needs by year for S0, split into amortization, interest, and
  overall deficit, with the liquidity-versus-solvency label.
- `outputs/DSA_TABLE.md`: the standard fan-chart table (debt, GFN, r minus g, primary, sfa_FX) for S0
  and the key stresses S1, S6, S7.

## Reading across the exhibits
- Debt paths: S0 converges below 90 at both valuations by 2029; S4, S6, S7 hold at or above the 90
  market line through 2029; S8 is the lowest path. Full commentary in `03_scenarios.md`.
- r minus g: negative in every year of every scenario except where the external stress (S4) lifts the
  effective rate; even there the carry stays below zero. The stabilizing primary is negative from 2027
  in the baseline, so no surplus is required to deleverage on the baseline (`05_bifurcation.md`).
- GFN: about 24 to 25 percent of GDP in 2026-27, near 20 percent thereafter, dominated by
  amortization. This is the liquidity constraint that the external disbursements and the liability
  swap address.

## Distributional overlay (tab_micro): pending, direction stated
The macro-to-micro pass through MFMod-microsim (occupational multinomial logit, Mincer earnings,
reweighting, sector-output rescaling, remittance assignment on the most recent EH survey) is not run
end to end in this pass. It is recorded as a pending item, not a result. The transmission direction
for the three scenarios that carry the sharpest household impact:
- **S3 (fuel cost-recovery)**: the January-2027 move to cost-recovery pricing (MEFP p.6, para 13) and
  the large-consumer diesel differential (Bs 18 versus Bs 9.80, DS 5676, p.5) raise transport and
  food prices; the incidence is regressive in the direct fuel budget share and mixed once transport
  pass-through is included. The magnitude is delegated to the companion fuel-incidence work order
  rather than re-derived here.
- **S5 (depreciation)**: a further real depreciation raises the price of tradables and imported food,
  a real-income loss concentrated in urban households with high imported-goods shares, partly offset
  in rural tradable-producing households.
- **S7 (combined)**: the deepest activity contraction, so the largest employment and labor-income
  channel, with the poverty headcount rising most in the trough year before the recovery.
The overlay tables (poverty headcount and loss by decile, urban and rural, per scenario) require the
microsim run and are left open with this direction recorded.
