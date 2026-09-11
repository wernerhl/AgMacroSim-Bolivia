"""
Step 5: Solve MFMod-BOL 2025-2027.
Simultaneous-block solver following WPS8965 structure:
  1. Demand side (C, I, X, M, G, stat/inv)
  2. Supply side: potential GDP (given K, L*, A_trend), output gap
  3. Prices (CPI Phillips curve, deflators)
  4. Labor market (wages, employment)
  5. Production accounts (sectoral VA)
  6. Fiscal block (revenue, expenditure, balance, debt dynamics)
  7. Balance of payments
  8. Monetary (endogenous policy rate under inflation-target proxy; BOL is pegged so flat)

Gauss-Seidel iteration within each year; loop year by year.
"""
import os
import json
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "Rawdata", "bol_data_extended.csv")
COEF = os.path.join(ROOT, "Rawdata", "bol_coefficients.json")
OUT  = os.path.join(ROOT, "Output", "BOLSoln.csv")
SUM  = os.path.join(ROOT, "Output", "BOL_projection_summary.csv")

CTY = "BOL"
def c(x): return f"{CTY}{x}"

ALPHA = 0.55   # labor share
DEPR  = 0.05

FORECAST = [2025, 2026, 2027]
MAX_ITER = 200
TOL = 1e-5

# ECM workhorse: applies Delta log(y_t) = alpha - theta*[log(y_{t-1}) - log(lr_{t-1})] + sum betas*d vars
def apply_ecm(y_prev, lr_prev, sr_deltas, coefs):
    """All args are scalars or numeric. sr_deltas is a dict of short-run delta log values
       matching keys of coefs['betas']."""
    if y_prev <= 0 or lr_prev <= 0:
        return y_prev
    ec = np.log(y_prev) - np.log(lr_prev)
    dlog_y = coefs["alpha"] - coefs["theta"] * ec
    for k, beta in coefs["betas"].items():
        if k in sr_deltas:
            dlog_y += beta * sr_deltas[k]
    # safety: clip to +/- 25% annual change
    dlog_y = np.clip(dlog_y, -0.25, 0.25)
    return y_prev * np.exp(dlog_y)

def main():
    d = pd.read_csv(DATA, index_col="year")
    d.index = d.index.astype(int)
    with open(COEF) as f:
        coef = json.load(f)

    print(f"Loaded data: {d.shape[0]} rows, {d.shape[1]} cols")
    print(f"Forecast years: {FORECAST}")

    for y in FORECAST:
        yp = y - 1  # previous year
        print(f"\n---- Solving year {y} ----")

        # Track iteration changes for convergence
        # Initialize current-year endogenous as y-1 scaled by nominal GDP growth guess
        # Use real potential growth as first guess
        dly_potl = np.log(d.loc[y-1, c("NYGDPTFP")] /
                          d.loc[yp, c("NYGDPTFP")]) + \
                   ALPHA * np.log(d.loc[y, c("LMEMPSTRL")] /
                                  d.loc[yp, c("LMEMPSTRL")]) + \
                   (1 - ALPHA) * np.log(d.loc[y-1, c("NEGDIKSTKKN")] /
                                        d.loc[yp-1, c("NEGDIKSTKKN")])

        # Initial guesses from previous year
        for col in [c("NECONPRVTKN"), c("NECONGOVTKN"), c("NEGDIFTOTKN"),
                    c("NEGDIFPRVKN"), c("NEGDIFGOVKN"),
                    c("NEEXPGNFSKN"), c("NEIMPGNFSKN"),
                    c("NYGDPMKTPKN"), c("NVAGRTOTLKN"), c("NVINDTOTLKN"),
                    c("NVSRVTOTLKN"), c("NYGDPFCSTKN"),
                    c("LMEMPTOTL"), c("NEWRTTOTLXN"),
                    c("FPCPITOTLXN"), c("NYGDPFCSTXN"),
                    c("NECONPRVTXN"), c("NECONGOVTXN"), c("NEGDIFTOTXN"),
                    c("NEEXPGNFSXN"), c("NEIMPGNFSXN")]:
            if pd.isna(d.loc[y, col]):
                d.loc[y, col] = d.loc[yp, col] * np.exp(dly_potl)

        # ======================================================
        # Gauss-Seidel iteration
        # ======================================================
        for it in range(MAX_ITER):
            prev = d.loc[y].copy()

            # ---- Capital stock (perpetual inventory) ----
            d.loc[y, c("NEGDIKSTKKN")] = (1 - DEPR) * d.loc[yp, c("NEGDIKSTKKN")] + \
                                         d.loc[y, c("NEGDIFTOTKN")]

            # ---- Potential GDP ----
            d.loc[y, c("NYGDPPOTLKN")] = (d.loc[y, c("NYGDPTFP")] *
                                         d.loc[y, c("LMEMPSTRL")] ** ALPHA *
                                         d.loc[yp, c("NEGDIKSTKKN")] ** (1 - ALPHA))

            # ---- Private consumption ECM ----
            # Long-run RHS: real disposable income proxy
            labinc_real = (ALPHA * d.loc[y, c("NYGDPFCSTCN")]) / d.loc[y, c("NECONPRVTXN")] \
                if not pd.isna(d.loc[y, c("NYGDPFCSTCN")]) else \
                d.loc[y, c("LMEMPTOTL")] * d.loc[y, c("NEWRTTOTLXN")] / d.loc[y, c("NECONPRVTXN")]
            dly_inc = np.log(labinc_real / (
                d.loc[yp, c("NYYWBTOTLCN")] / d.loc[yp, c("NECONPRVTXN")]))
            dly_gdp = np.log(d.loc[y, c("NYGDPMKTPKN")] / d.loc[yp, c("NYGDPMKTPKN")])
            d.loc[y, c("NECONPRVTKN")] = apply_ecm(
                d.loc[yp, c("NECONPRVTKN")],
                d.loc[yp, c("NYYWBTOTLCN")] / d.loc[yp, c("NECONPRVTXN")],
                {"dly_inc": dly_inc, "dly_gdp": dly_gdp},
                coef["NECONPRVTKN"])

            # ---- Govt consumption: real = nominal / deflator ----
            # Assume govt consumption nominal grows with spending (pinned to nominal GDP growth)
            dly_ngdp = np.log(d.loc[y, c("NYGDPMKTPCN")] / d.loc[yp, c("NYGDPMKTPCN")]) \
                if not pd.isna(d.loc[y, c("NYGDPMKTPCN")]) else dly_potl + 0.03
            d.loc[y, c("NECONGOVTCN")] = d.loc[yp, c("NECONGOVTCN")] * np.exp(dly_ngdp)
            d.loc[y, c("NECONGOVTKN")] = d.loc[y, c("NECONGOVTCN")] / d.loc[y, c("NECONGOVTXN")]

            # ---- Private investment ECM ----
            dly_rate = 0.0  # rate held flat
            d.loc[y, c("NEGDIFPRVKN")] = apply_ecm(
                d.loc[yp, c("NEGDIFPRVKN")],
                d.loc[yp, c("NYGDPPOTLKN")],
                {"dly_gdp": dly_gdp, "dly_rate": dly_rate},
                coef["NEGDIFPRVKN"])

            # ---- Public investment: grow with nominal GDP (fiscal rule) ----
            d.loc[y, c("NEGDIFGOVCN")] = d.loc[yp, c("NEGDIFGOVCN")] * np.exp(dly_ngdp)
            d.loc[y, c("NEGDIFGOVKN")] = d.loc[y, c("NEGDIFGOVCN")] / d.loc[y, c("NEGDIFTOTXN")]

            # ---- Total fixed investment ----
            d.loc[y, c("NEGDIFTOTKN")] = d.loc[y, c("NEGDIFPRVKN")] + d.loc[y, c("NEGDIFGOVKN")]

            # ---- Exports ECM ----
            dly_xmkt = np.log(d.loc[y, c("XMKT_USD")] / d.loc[yp, c("XMKT_USD")])
            d.loc[y, c("NEEXPGNFSKN")] = apply_ecm(
                d.loc[yp, c("NEEXPGNFSKN")],
                d.loc[yp, c("XMKT_USD")],
                {"dly_xmkt": dly_xmkt},
                coef["NEEXPGNFSKN"])
            # Bolivia-specific: apply gas-sector decline (3%/year structural)
            d.loc[y, c("NEEXPGNFSKN")] *= 0.97

            # ---- Imports ECM ----
            gde_prev = (d.loc[yp, c("NECONPRVTKN")] + d.loc[yp, c("NECONGOVTKN")]
                        + d.loc[yp, c("NEGDIFTOTKN")] + d.loc[yp, c("NEEXPGNFSKN")])
            gde_cur  = (d.loc[y, c("NECONPRVTKN")] + d.loc[y, c("NECONGOVTKN")]
                        + d.loc[y, c("NEGDIFTOTKN")] + d.loc[y, c("NEEXPGNFSKN")])
            dly_gde = np.log(gde_cur / gde_prev)
            d.loc[y, c("NEIMPGNFSKN")] = apply_ecm(
                d.loc[yp, c("NEIMPGNFSKN")],
                gde_prev,
                {"dly_gde": dly_gde},
                coef["NEIMPGNFSKN"])

            # ---- GDP identity (real) ----
            d.loc[y, c("NYGDPMKTPKN")] = (d.loc[y, c("NECONPRVTKN")]
                                        + d.loc[y, c("NECONGOVTKN")]
                                        + d.loc[y, c("NEGDIFTOTKN")]
                                        + d.loc[y, c("NEGDISTKBKN")]
                                        + d.loc[y, c("NEEXPGNFSKN")]
                                        - d.loc[y, c("NEIMPGNFSKN")]
                                        + d.loc[y, c("NYGDPDISCKN")])

            # ---- Output gap ----
            d.loc[y, c("NYGDPGAP_")] = (d.loc[y, c("NYGDPMKTPKN")] /
                                       d.loc[y, c("NYGDPPOTLKN")] - 1) * 100

            # ---- Production accounts ----
            d.loc[y, c("NVAGRTOTLKN")] = apply_ecm(
                d.loc[yp, c("NVAGRTOTLKN")],
                d.loc[yp, c("NYGDPPOTLKN")],
                {"dly_gde": dly_gde},
                coef["NVAGRTOTLKN"])
            d.loc[y, c("NVINDTOTLKN")] = apply_ecm(
                d.loc[yp, c("NVINDTOTLKN")],
                d.loc[yp, c("NYGDPPOTLKN")],
                {"dly_gde": dly_gde},
                coef["NVINDTOTLKN"])
            # Services as balancing identity (WPS8965 eq 53)
            d.loc[y, c("NYGDPFCSTKN")] = d.loc[y, c("NYGDPMKTPKN")] - d.loc[y, c("NYTAXNINDKN")] \
                if not pd.isna(d.loc[y, c("NYTAXNINDKN")]) else d.loc[y, c("NYGDPMKTPKN")] * 0.92
            d.loc[y, c("NVSRVTOTLKN")] = (d.loc[y, c("NYGDPFCSTKN")]
                                         - d.loc[y, c("NVAGRTOTLKN")]
                                         - d.loc[y, c("NVINDTOTLKN")])

            # ---- Prices: CPI (Phillips-curve-like) ----
            # Simplified: pi_t = pi_{t-1}*0.5 + 0.5*target + beta*gap
            pi_lag = np.log(d.loc[yp, c("FPCPITOTLXN")] / d.loc[yp-1, c("FPCPITOTLXN")])
            pi_target = 0.03  # Bolivia's historical core inflation anchor
            gap = d.loc[y, c("NYGDPGAP_")] / 100
            pi_t = 0.5 * pi_lag + 0.5 * pi_target + 0.15 * gap
            pi_t = np.clip(pi_t, -0.02, 0.20)
            d.loc[y, c("FPCPITOTLXN")] = d.loc[yp, c("FPCPITOTLXN")] * np.exp(pi_t)

            # ---- Deflators (track CPI with persistence) ----
            for p in [c("NYGDPFCSTXN"), c("NECONPRVTXN"), c("NECONGOVTXN"),
                      c("NEGDIFTOTXN"), c("NVAGRTOTLXN"), c("NVINDTOTLXN"), c("NVSRVTOTLXN")]:
                d.loc[y, p] = d.loc[yp, p] * (1 + pi_t)
            # Import/export deflators: track world (flat USD inflation 2%) x FX (peg flat)
            d.loc[y, c("NEIMPGNFSXN")] = d.loc[yp, c("NEIMPGNFSXN")] * (1 + 0.02)
            d.loc[y, c("NEEXPGNFSXN")] = d.loc[yp, c("NEEXPGNFSXN")] * (1 + 0.01)  # gas prices weaker
            # GDP at market prices deflator
            d.loc[y, c("NYGDPMKTPXN")] = d.loc[yp, c("NYGDPMKTPXN")] * (1 + pi_t)

            # ---- Nominal GDP (identity) ----
            d.loc[y, c("NYGDPMKTPCN")] = d.loc[y, c("NYGDPMKTPKN")] * d.loc[y, c("NYGDPMKTPXN")]
            d.loc[y, c("NYGDPFCSTCN")] = d.loc[y, c("NYGDPFCSTKN")] * d.loc[y, c("NYGDPFCSTXN")]
            d.loc[y, c("NECONPRVTCN")] = d.loc[y, c("NECONPRVTKN")] * d.loc[y, c("NECONPRVTXN")]
            d.loc[y, c("NECONGOVTCN")] = d.loc[y, c("NECONGOVTKN")] * d.loc[y, c("NECONGOVTXN")]
            d.loc[y, c("NEGDIFTOTCN")] = d.loc[y, c("NEGDIFTOTKN")] * d.loc[y, c("NEGDIFTOTXN")]
            d.loc[y, c("NEEXPGNFSCN")] = d.loc[y, c("NEEXPGNFSKN")] * d.loc[y, c("NEEXPGNFSXN")]
            d.loc[y, c("NEIMPGNFSCN")] = d.loc[y, c("NEIMPGNFSKN")] * d.loc[y, c("NEIMPGNFSXN")]
            d.loc[y, c("NYTAXNINDCN")] = d.loc[y, c("NYGDPMKTPCN")] - d.loc[y, c("NYGDPFCSTCN")]
            d.loc[y, c("NVAGRTOTLCN")] = d.loc[y, c("NVAGRTOTLKN")] * d.loc[y, c("NVAGRTOTLXN")]
            d.loc[y, c("NVINDTOTLCN")] = d.loc[y, c("NVINDTOTLKN")] * d.loc[y, c("NVINDTOTLXN")]
            d.loc[y, c("NVSRVTOTLCN")] = d.loc[y, c("NVSRVTOTLKN")] * d.loc[y, c("NVSRVTOTLXN")]

            # ---- Labor market ----
            # Wages: track CPI + productivity
            prod_growth = np.log(d.loc[y, c("NYGDPMKTPKN")] / d.loc[y, c("LMEMPSTRL")] /
                                 (d.loc[yp, c("NYGDPMKTPKN")] / d.loc[yp, c("LMEMPSTRL")]))
            d.loc[y, c("NEWRTTOTLXN")] = d.loc[yp, c("NEWRTTOTLXN")] * np.exp(pi_t + 0.5 * prod_growth)
            d.loc[y, c("NYYWBTOTLCN")] = d.loc[y, c("NEWRTTOTLXN")] * d.loc[y, c("LMEMPTOTL")]
            # Employment ECM
            d.loc[y, c("LMEMPTOTL")] = apply_ecm(
                d.loc[yp, c("LMEMPTOTL")],
                d.loc[y, c("LMEMPSTRL")],
                {"gap_chg": gap, "dly_lstar": np.log(d.loc[y, c("LMEMPSTRL")] /
                                                    d.loc[yp, c("LMEMPSTRL")])},
                coef["LMEMPTOTL"])
            d.loc[y, c("LMUNRTOTL_")] = (1 - d.loc[y, c("LMEMPTOTL")] /
                                         d.loc[y, c("LMLBFTOTL")]) * 100

            # ---- Fiscal ----
            # Revenue: effective rate * base (base = nominal GDP)  [WPS8965 eq 31, BAU]
            rev_rate_hist = d.loc[2024, c("GGREVTOTLCN")] / d.loc[2024, c("NYGDPMKTPCN")]
            d.loc[y, c("GGREVTOTLCN")] = rev_rate_hist * d.loc[y, c("NYGDPMKTPCN")]
            d.loc[y, c("GGREVTAXTCN")] = (d.loc[2024, c("GGREVTAXTCN")] /
                                         d.loc[2024, c("NYGDPMKTPCN")]) * d.loc[y, c("NYGDPMKTPCN")]
            d.loc[y, c("GGREVDRCTCN")] = 0.28 * d.loc[y, c("GGREVTAXTCN")]
            d.loc[y, c("GGREVIDRTCN")] = 0.72 * d.loc[y, c("GGREVTAXTCN")]

            # Expenditure: grows with nominal GDP (ECM result)
            exp_rate_hist = d.loc[2024, c("GGEXPTOTLCN")] / d.loc[2024, c("NYGDPMKTPCN")]
            # Allow partial adjustment toward gradual consolidation (Bolivia fiscal stress 2024-2025)
            d.loc[y, c("GGEXPTOTLCN")] = exp_rate_hist * d.loc[y, c("NYGDPMKTPCN")]

            # Interest payments: rate * prior-period debt
            int_rate_hist = d.loc[2024, c("GGEXPINTPCN")] / d.loc[2024-1, c("GGDBTTOTLCN")]
            d.loc[y, c("GGEXPINTPCN")] = int_rate_hist * d.loc[yp, c("GGDBTTOTLCN")]

            # Balance = R - G
            d.loc[y, c("GGBALOVRLCN")] = d.loc[y, c("GGREVTOTLCN")] - d.loc[y, c("GGEXPTOTLCN")]
            # Primary balance = R - (G - Interest)
            d.loc[y, c("GGBALPRIMCN")] = d.loc[y, c("GGREVTOTLCN")] - \
                                         (d.loc[y, c("GGEXPTOTLCN")] - d.loc[y, c("GGEXPINTPCN")])
            # Debt dynamics: D_t = D_{t-1} - BB (deficit adds to debt)
            d.loc[y, c("GGDBTTOTLCN")] = d.loc[yp, c("GGDBTTOTLCN")] - d.loc[y, c("GGBALOVRLCN")]
            d.loc[y, c("GGDBTEXTLCN")] = 0.55 * d.loc[y, c("GGDBTTOTLCN")]
            d.loc[y, c("GGDBTDOMTCN")] = 0.45 * d.loc[y, c("GGDBTTOTLCN")]
            d.loc[y, c("GGBALOVRLGD")] = d.loc[y, c("GGBALOVRLCN")] / d.loc[y, c("NYGDPMKTPCN")] * 100
            d.loc[y, c("GGDBTTOTLGD")] = d.loc[y, c("GGDBTTOTLCN")] / d.loc[y, c("NYGDPMKTPCN")] * 100

            # ---- Balance of Payments ----
            # Exports/imports USD (via nominal LCU / FX)
            d.loc[y, c("BXGSRMRCHCD")] = (d.loc[y, c("NEEXPGNFSCN")] / d.loc[y, c("PANUSATLS")]) * \
                (d.loc[2024, c("BXGSRMRCHCD")] * d.loc[2024, c("PANUSATLS")] / d.loc[2024, c("NEEXPGNFSCN")])
            d.loc[y, c("BMGSRMRCHCD")] = (d.loc[y, c("NEIMPGNFSCN")] / d.loc[y, c("PANUSATLS")]) * \
                (d.loc[2024, c("BMGSRMRCHCD")] * d.loc[2024, c("PANUSATLS")] / d.loc[2024, c("NEIMPGNFSCN")])
            # Remittances: grow with world GDP USD proxy
            d.loc[y, c("BXFSTREMTCD")] = d.loc[yp, c("BXFSTREMTCD")] * (d.loc[y, c("XMKT_USD")] /
                                                                       d.loc[yp, c("XMKT_USD")])
            # Current account = trade balance + remittances + other (held as share of GDP USD)
            trade_bal = d.loc[y, c("BXGSRMRCHCD")] - d.loc[y, c("BMGSRMRCHCD")]
            d.loc[y, c("NYGDPMKTPCD")] = d.loc[y, c("NYGDPMKTPCN")] / d.loc[y, c("PANUSATLS")]
            other_cab_gdp = (d.loc[2024, c("BNCABFUNDCD")] - (d.loc[2024, c("BXGSRMRCHCD")] -
                            d.loc[2024, c("BMGSRMRCHCD")])) / d.loc[2024, c("NYGDPMKTPCD")]
            d.loc[y, c("BNCABFUNDCD")] = trade_bal + other_cab_gdp * d.loc[y, c("NYGDPMKTPCD")]

            # ---- Convergence ----
            key = [c("NYGDPMKTPKN"), c("NECONPRVTKN"), c("NEGDIFTOTKN"),
                   c("NEEXPGNFSKN"), c("NEIMPGNFSKN"), c("FPCPITOTLXN")]
            cur = d.loc[y, key].astype(float)
            old = prev[key].astype(float)
            if (old == 0).any():
                continue
            diff = ((cur - old) / old).abs().max()
            if diff < TOL:
                print(f"  Converged in {it+1} iterations, max rel diff = {diff:.2e}")
                break
        else:
            print(f"  WARN: did not converge after {MAX_ITER} iter (max diff={diff:.2e})")

        # Report
        print(f"  Real GDP growth   = {100*(np.exp(np.log(d.loc[y,c('NYGDPMKTPKN')]/d.loc[yp,c('NYGDPMKTPKN')])) - 1):.2f}%")
        print(f"  CPI inflation     = {100*np.log(d.loc[y,c('FPCPITOTLXN')]/d.loc[yp,c('FPCPITOTLXN')]):.2f}%")
        print(f"  Fiscal bal % GDP  = {d.loc[y,c('GGBALOVRLGD')]:.2f}%")
        print(f"  Debt % GDP        = {d.loc[y,c('GGDBTTOTLGD')]:.2f}%")
        print(f"  Current acc USD m = {d.loc[y,c('BNCABFUNDCD')]/1e6:.0f}")

    # Save full solution
    d.to_csv(OUT)
    print(f"\nFull solution written to {OUT}")

    # Summary table
    rows = []
    for y in range(2020, 2028):
        if y not in d.index: continue
        yp = y - 1
        row = {
            "year": y,
            "Real GDP (bn Bs, 2015)":   d.loc[y, c("NYGDPMKTPKN")] / 1e9,
            "Real GDP growth %":        100 * (d.loc[y, c("NYGDPMKTPKN")] / d.loc[yp, c("NYGDPMKTPKN")] - 1),
            "Nominal GDP (bn Bs)":      d.loc[y, c("NYGDPMKTPCN")] / 1e9,
            "Nominal GDP (bn USD)":     d.loc[y, c("NYGDPMKTPCN")] / d.loc[y, c("PANUSATLS")] / 1e9,
            "CPI inflation %":          100 * (d.loc[y, c("FPCPITOTLXN")] / d.loc[yp, c("FPCPITOTLXN")] - 1),
            "Output gap %":             d.loc[y, c("NYGDPGAP_")],
            "Fiscal bal % GDP":         d.loc[y, c("GGBALOVRLGD")],
            "Public debt % GDP":        d.loc[y, c("GGDBTTOTLGD")],
            "Current acc USD bn":       d.loc[y, c("BNCABFUNDCD")] / 1e9,
            "Employment (millions)":    d.loc[y, c("LMEMPTOTL")] / 1e6,
            "Unemployment rate":        d.loc[y, c("LMUNRTOTL_")],
            "Private consumption g%":   100 * (d.loc[y, c("NECONPRVTKN")] / d.loc[yp, c("NECONPRVTKN")] - 1),
            "Private investment g%":    100 * (d.loc[y, c("NEGDIFPRVKN")] / d.loc[yp, c("NEGDIFPRVKN")] - 1),
            "Real exports g%":          100 * (d.loc[y, c("NEEXPGNFSKN")] / d.loc[yp, c("NEEXPGNFSKN")] - 1),
            "Real imports g%":          100 * (d.loc[y, c("NEIMPGNFSKN")] / d.loc[yp, c("NEIMPGNFSKN")] - 1),
            "Agr real g%":              100 * (d.loc[y, c("NVAGRTOTLKN")] / d.loc[yp, c("NVAGRTOTLKN")] - 1),
            "Ind real g%":              100 * (d.loc[y, c("NVINDTOTLKN")] / d.loc[yp, c("NVINDTOTLKN")] - 1),
            "Srv real g%":              100 * (d.loc[y, c("NVSRVTOTLKN")] / d.loc[yp, c("NVSRVTOTLKN")] - 1),
        }
        rows.append(row)
    summ = pd.DataFrame(rows).set_index("year")
    summ.to_csv(SUM)

    print("\n" + "=" * 70)
    print("MFMod-BOL PROJECTION SUMMARY")
    print("=" * 70)
    print(summ.T.round(2).to_string())

if __name__ == "__main__":
    main()
