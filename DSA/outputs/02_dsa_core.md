# 02 Debt-dynamics core

## Identity
The gross public-debt ratio evolves as
```
b_t = ((1 + r_t)/(1 + g_t)) * b_{t-1} - pb_t + sfa_t
```
with the change
```
Δb_t ≈ ((r_t - g_t)/(1 + g_t)) * b_{t-1} - pb_t + sfa_t
```
where b is SPNF gross debt to GDP, r the effective real interest rate on the debt, g real growth, pb
the primary balance to GDP, and sfa the stock-flow adjustment. r is coupon-based; the exchange-rate
revaluation is not in r, it is in sfa.

## The sfa term is not a residual for Bolivia
```
sfa_FX,t = share_FX * b_{t-1} * (Δe_t / (1 + Δe_t))
```
with share_FX = 0.31 and Δe the change in the valuation rate. The official-rate unification in 2026
(peg 6.96 to reference about 9.8, Δe about 0.41) produces sfa_FX of about 7 points of GDP on the
official-valued stock in that year, which is the mechanical rise the MEFP describes (p.3, para 7).
Contingent-liability crystallization enters as a separate switched term sfa_CL, off in S0 and set in
S6.

Implementation and the split between r and sfa are consistent: for the foreign-currency portion the
real cost in domestic terms is (coupon minus domestic inflation) in r plus (depreciation) in sfa_FX,
which sums to the correct (coupon plus depreciation minus inflation). No double count.

## Per-year quantities (S0, official valuation)
Source table `exhibits/tab_rminusg.md` and `exhibits/tab_gfn.md`.

- **r minus g** is negative throughout: about minus 8.6 in 2026, minus 5.5 in 2027, minus 4.5 in
  2028, minus 3.3 in 2029, minus 2.5 in 2030, settling near minus 2 by 2035. The effective real rate
  is deeply negative early (nominal about 3 percent against inflation 14 percent) and rises toward
  zero as inflation normalizes; growth turns positive from 2028. The carry stays negative because the
  effective coupon is low.
- **Stabilizing growth g\*** (the growth that sets Δb to zero given that year's r, pb, sfa): about 7.5
  percent in 2026 (the FX-shock year, unattainable by growth alone), then falls below the projected
  growth from 2027 on, so the ratio declines at the projected growth in every subsequent year.
- **Stabilizing primary pb\***: +0.2 percent in 2026 (a small surplus, the revaluation year), then
  negative from 2027 (minus 4.8, minus 3.8, minus 2.7, trending to minus 1.4 by 2035). The programmed
  primary is tighter than pb\* from 2027 on; the gap is the room by which the ratio falls.
- **Gross financing needs** (amortization plus interest plus overall deficit): about 24 to 25 percent
  of GDP in 2026-27, settling near 20 percent. Amortization (domestic rollover plus external) is the
  larger part, about 12 to 14 points; interest is 2.4 to 3.6 points; the overall deficit falls from
  8.9 to 3.5 points. Identified financing is the IFI disbursements consistent with the reserve floors
  (Cuadro 1, p.17), the USD 1 bn bond (p.2), and domestic issuance; a residual financing gap opens in
  the external-downside stress (S4) when disbursements slip.

## Solvency versus liquidity
The negative carry makes the stock trajectory favorable (a solvency reading): the ratio declines on
the program's primary path without a surplus. The gross financing need near 20 to 25 percent of GDP is
a liquidity reading: the economy has to roll a fifth to a quarter of GDP each year, most of it
domestic, some external. The two readings diverge, and the program's external financing, reserve
accumulation, and the external-to-local liability swap address the liquidity side while the carry
handles the solvency side. This distinction is the frame for the scenarios: S1 to S3 and S8 act on the
solvency side (g and pb), S4 to S6 act on the liquidity and stock side (r, sfa_FX, sfa_CL).
