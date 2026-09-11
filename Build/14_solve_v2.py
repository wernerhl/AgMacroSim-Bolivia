"""
MFMod-BOL v2 — Solver 2025-2027 with all architectural fixes:
  1. CPI via Phillips + reserve-scarcity × BCB-financing channel
  2. BCB financing pinned to fiscal residual (primary deficit less external financing)
  3. Fuel-subsidy block added to expenditure
  4. Hydrocarbon-revenue erosion (structural decline in IDH + IEHD)
  5. Export gas sub-component declines at 15%/yr volume
  6. Investment α clipped to 0 (no indefinite drift)
  7. NFPS debt perimeter throughout
"""
import os, json
import numpy as np
import pandas as pd

ROOT = "/Users/whl/Documents/whl.BolBudget/MFMOD_BOL"
DATA = os.path.join(ROOT, "Rawdata", "bol_data_extended_v2.csv")
COEF = os.path.join(ROOT, "Rawdata", "bol_coefficients_v2.json")
OUT  = os.path.join(ROOT, "Output", "BOLSoln_v2.csv")
SUM  = os.path.join(ROOT, "Output", "BOL_MFMod_v2_projections.csv")
CMP  = os.path.join(ROOT, "Output", "BOL_MFMod_v2_vs_IMF.csv")

CTY = "BOL"
def c(x): return f"{CTY}{x}"
ALPHA = 0.55
DEPR  = 0.05
FORECAST = [2025, 2026, 2027]
MAX_ITER = 300
TOL = 1e-5

def apply_ecm(y_prev, lr_prev, sr_deltas, coefs):
    if y_prev <= 0 or lr_prev <= 0:
        return y_prev
    ec = np.log(y_prev) - np.log(lr_prev)
    dlog_y = coefs.get("alpha", 0) - coefs.get("theta", 0.2) * ec
    for k, beta in coefs.get("betas", {}).items():
        if k in sr_deltas:
            dlog_y += beta * sr_deltas[k]
    dlog_y = np.clip(dlog_y, -0.25, 0.25)
    return y_prev * np.exp(dlog_y)

def main():
    d = pd.read_csv(DATA, index_col="year")
    d.index = d.index.astype(int)
    with open(COEF) as f:
        coef = json.load(f)

    # Gas share of exports in 2024 base
    GAS_SHARE_EXP = 0.20  # hydrocarbon share of goods exports, IMF 2024
    NON_GAS_SHARE = 1 - GAS_SHARE_EXP

    for y in FORECAST:
        yp = y - 1
        print(f"\n---- v2 Solving {y} ----")

        # Initial guess for endogenous current-year values
        g_potl = (np.log(d.loc[y-1, c("NYGDPTFP")] / d.loc[yp, c("NYGDPTFP")])
                + ALPHA * np.log(d.loc[y, c("LMEMPSTRL")] / d.loc[yp, c("LMEMPSTRL")])
                + (1 - ALPHA) * np.log(d.loc[yp, c("NEGDIKSTKKN")] / d.loc[yp-1, c("NEGDIKSTKKN")]))

        # Broad fallback: for any numeric column NaN in year y, initialize from year yp
        # scaled by initial nominal-growth guess.
        init_guess = float(np.exp(g_potl + 0.15))  # ~15% nominal growth first guess
        for col in d.columns:
            if pd.isna(d.loc[y, col]):
                prev_val = d.loc[yp, col] if yp in d.index else np.nan
                if pd.notna(prev_val) and isinstance(prev_val, (int, float, np.floating)):
                    if prev_val > 0:
                        d.loc[y, col] = prev_val * init_guess
                    else:
                        d.loc[y, col] = prev_val

        # Gauss-Seidel
        diff = np.inf
        for it in range(MAX_ITER):
            prev_state = d.loc[y].copy()

            # Capital stock
            d.loc[y, c("NEGDIKSTKKN")] = (1 - DEPR) * d.loc[yp, c("NEGDIKSTKKN")] + \
                                         d.loc[y, c("NEGDIFTOTKN")]
            # Potential GDP
            d.loc[y, c("NYGDPPOTLKN")] = (d.loc[y, c("NYGDPTFP")] *
                                          d.loc[y, c("LMEMPSTRL")] ** ALPHA *
                                          d.loc[yp, c("NEGDIKSTKKN")] ** (1 - ALPHA))

            # Private consumption
            labinc_real = ALPHA * d.loc[y, c("NYGDPFCSTCN")] / d.loc[y, c("NECONPRVTXN")]
            dly_inc = np.log(labinc_real / (ALPHA * d.loc[yp, c("NYGDPFCSTCN")] /
                                           d.loc[yp, c("NECONPRVTXN")]))
            dly_gdp = np.log(d.loc[y, c("NYGDPMKTPKN")] / d.loc[yp, c("NYGDPMKTPKN")])
            d.loc[y, c("NECONPRVTKN")] = apply_ecm(
                d.loc[yp, c("NECONPRVTKN")],
                ALPHA * d.loc[yp, c("NYGDPFCSTCN")] / d.loc[yp, c("NECONPRVTXN")],
                {"dly_inc": dly_inc, "dly_gdp": dly_gdp},
                coef["NECONPRVTKN"])

            # Govt consumption: nominal pinned to nominal GDP growth
            dly_ngdp = np.log(d.loc[y, c("NYGDPMKTPCN")] / d.loc[yp, c("NYGDPMKTPCN")]) \
                if d.loc[y, c("NYGDPMKTPCN")] > 0 else g_potl + 0.15
            d.loc[y, c("NECONGOVTCN")] = d.loc[yp, c("NECONGOVTCN")] * np.exp(dly_ngdp)
            d.loc[y, c("NECONGOVTKN")] = d.loc[y, c("NECONGOVTCN")] / d.loc[y, c("NECONGOVTXN")]

            # Private investment (α=0 from v2 estimation)
            # Break feedback: use potential-GDP growth in SR (not actual GDP) to avoid
            # the self-reinforcing contraction from actual_GDP = f(I).
            dly_potl_y = np.log(d.loc[y, c("NYGDPPOTLKN")] / d.loc[yp, c("NYGDPPOTLKN")])
            d.loc[y, c("NEGDIFPRVKN")] = apply_ecm(
                d.loc[yp, c("NEGDIFPRVKN")], d.loc[yp, c("NYGDPPOTLKN")],
                {"dly_gdp": dly_potl_y, "dly_rate": 0.0},
                coef["NEGDIFPRVKN"])
            # Public investment: nominal grows with nominal GDP
            d.loc[y, c("NEGDIFGOVCN")] = d.loc[yp, c("NEGDIFGOVCN")] * np.exp(dly_ngdp)
            d.loc[y, c("NEGDIFGOVKN")] = d.loc[y, c("NEGDIFGOVCN")] / d.loc[y, c("NEGDIFTOTXN")]
            d.loc[y, c("NEGDIFTOTKN")] = d.loc[y, c("NEGDIFPRVKN")] + d.loc[y, c("NEGDIFGOVKN")]

            # Exports: non-gas grows with world; gas declines 15%/yr
            dly_xmkt = np.log(d.loc[y, c("XMKT_USD")] / d.loc[yp, c("XMKT_USD")])
            exp_lag = d.loc[yp, c("NEEXPGNFSKN")]
            non_gas_new = apply_ecm(
                NON_GAS_SHARE * exp_lag,
                NON_GAS_SHARE * d.loc[yp, c("XMKT_USD")],
                {"dly_xmkt": dly_xmkt},
                coef["NEEXPGNFSKN"])
            gas_new = GAS_SHARE_EXP * exp_lag * (1 + d.loc[y, c("GAS_VOL_GR")])
            d.loc[y, c("NEEXPGNFSKN")] = non_gas_new + gas_new
            # Share erodes over time (gas -> 0)
            GAS_SHARE_EXP = max(GAS_SHARE_EXP * 0.90, 0.01)

            # Imports
            gde_prev = (d.loc[yp, c("NECONPRVTKN")] + d.loc[yp, c("NECONGOVTKN")]
                        + d.loc[yp, c("NEGDIFTOTKN")] + d.loc[yp, c("NEEXPGNFSKN")])
            gde_cur  = (d.loc[y, c("NECONPRVTKN")] + d.loc[y, c("NECONGOVTKN")]
                        + d.loc[y, c("NEGDIFTOTKN")] + d.loc[y, c("NEEXPGNFSKN")])
            dly_gde = np.log(gde_cur / gde_prev)
            d.loc[y, c("NEIMPGNFSKN")] = apply_ecm(
                d.loc[yp, c("NEIMPGNFSKN")], gde_prev,
                {"dly_gde": dly_gde}, coef["NEIMPGNFSKN"])
            # Bolivia 2025-26: FX scarcity compresses imports by extra 3-5% per IMF Text Table 3
            # (imports of G&S: 23.4% GDP 2024 -> 20.4% 2025 -> 18.9% 2026)
            if y == 2025: d.loc[y, c("NEIMPGNFSKN")] *= 0.95
            if y >= 2026: d.loc[y, c("NEIMPGNFSKN")] *= 0.97

            # Real GDP identity
            d.loc[y, c("NYGDPMKTPKN")] = (d.loc[y, c("NECONPRVTKN")]
                                        + d.loc[y, c("NECONGOVTKN")]
                                        + d.loc[y, c("NEGDIFTOTKN")]
                                        + d.loc[y, c("NEGDISTKBKN")]
                                        + d.loc[y, c("NEEXPGNFSKN")]
                                        - d.loc[y, c("NEIMPGNFSKN")]
                                        + d.loc[y, c("NYGDPDISCKN")])
            d.loc[y, c("NYGDPGAP_")] = (d.loc[y, c("NYGDPMKTPKN")] /
                                        d.loc[y, c("NYGDPPOTLKN")] - 1) * 100

            # Production
            d.loc[y, c("NVAGRTOTLKN")] = apply_ecm(
                d.loc[yp, c("NVAGRTOTLKN")], d.loc[yp, c("NYGDPPOTLKN")],
                {"dly_gde": dly_gde}, coef["NVAGRTOTLKN"])
            d.loc[y, c("NVINDTOTLKN")] = apply_ecm(
                d.loc[yp, c("NVINDTOTLKN")], d.loc[yp, c("NYGDPPOTLKN")],
                {"dly_gde": dly_gde}, coef["NVINDTOTLKN"])
            d.loc[y, c("NYGDPFCSTKN")] = d.loc[y, c("NYGDPMKTPKN")] * 0.92  # simple factor-cost
            d.loc[y, c("NVSRVTOTLKN")] = (d.loc[y, c("NYGDPFCSTKN")]
                                        - d.loc[y, c("NVAGRTOTLKN")]
                                        - d.loc[y, c("NVINDTOTLKN")])

            # ==============================================================
            # CPI — Phillips + Reserve-scarcity × BCB-financing channel
            # ==============================================================
            pi_lag = np.log(d.loc[yp, c("FPCPITOTLXN")] / d.loc[yp-1, c("FPCPITOTLXN")])
            gap = d.loc[y, c("NYGDPGAP_")] / 100
            # Estimate of BCB financing as % of GDP this year
            # — feedback loop: we need this after fiscal block; here use prior-iter value
            bcb_fin_gdp_prev = d.loc[y, c("GGFINBCBGD")] if c("GGFINBCBGD") in d.columns and \
                              pd.notna(d.loc[y].get(c("GGFINBCBGD"), np.nan)) else 10.0
            scar = d.loc[y, c("RES_SCARCITY")]
            cpi_coef = coef["FPCPITOTLXN"]
            pi_t = (cpi_coef["alpha"]
                  + cpi_coef["pi_lag"] * pi_lag
                  + cpi_coef["gap"] * gap
                  + cpi_coef["fin_scar"] * scar * (bcb_fin_gdp_prev / 100))
            pi_t = np.clip(pi_t, -0.03, 0.40)
            d.loc[y, c("FPCPITOTLXN")] = d.loc[yp, c("FPCPITOTLXN")] * np.exp(pi_t)

            # Deflators
            for p in [c("NYGDPFCSTXN"), c("NECONPRVTXN"), c("NECONGOVTXN"),
                      c("NEGDIFTOTXN"), c("NVAGRTOTLXN"), c("NVINDTOTLXN"), c("NVSRVTOTLXN")]:
                d.loc[y, p] = d.loc[yp, p] * np.exp(pi_t)
            d.loc[y, c("NEIMPGNFSXN")] = d.loc[yp, c("NEIMPGNFSXN")] * np.exp(0.02 + 0.4 * pi_t)
            d.loc[y, c("NEEXPGNFSXN")] = d.loc[yp, c("NEEXPGNFSXN")] * np.exp(0.01 + 0.3 * pi_t)
            d.loc[y, c("NYGDPMKTPXN")] = d.loc[yp, c("NYGDPMKTPXN")] * np.exp(pi_t)

            # Nominal side
            d.loc[y, c("NYGDPMKTPCN")] = d.loc[y, c("NYGDPMKTPKN")] * d.loc[y, c("NYGDPMKTPXN")]
            d.loc[y, c("NYGDPFCSTCN")] = d.loc[y, c("NYGDPFCSTKN")] * d.loc[y, c("NYGDPFCSTXN")]
            d.loc[y, c("NECONPRVTCN")] = d.loc[y, c("NECONPRVTKN")] * d.loc[y, c("NECONPRVTXN")]
            d.loc[y, c("NECONGOVTCN")] = d.loc[y, c("NECONGOVTKN")] * d.loc[y, c("NECONGOVTXN")]
            d.loc[y, c("NEGDIFTOTCN")] = d.loc[y, c("NEGDIFTOTKN")] * d.loc[y, c("NEGDIFTOTXN")]
            d.loc[y, c("NEEXPGNFSCN")] = d.loc[y, c("NEEXPGNFSKN")] * d.loc[y, c("NEEXPGNFSXN")]
            d.loc[y, c("NEIMPGNFSCN")] = d.loc[y, c("NEIMPGNFSKN")] * d.loc[y, c("NEIMPGNFSXN")]

            # Labor
            prod_g = np.log(d.loc[y, c("NYGDPMKTPKN")] / d.loc[y, c("LMEMPSTRL")] /
                            (d.loc[yp, c("NYGDPMKTPKN")] / d.loc[yp, c("LMEMPSTRL")]))
            d.loc[y, c("NEWRTTOTLXN")] = d.loc[yp, c("NEWRTTOTLXN")] * np.exp(pi_t + 0.5 * prod_g)
            d.loc[y, c("NYYWBTOTLCN")] = d.loc[y, c("NEWRTTOTLXN")] * d.loc[y, c("LMEMPTOTL")]
            d.loc[y, c("LMEMPTOTL")] = apply_ecm(
                d.loc[yp, c("LMEMPTOTL")], d.loc[y, c("LMEMPSTRL")],
                {"gap_chg": gap, "dly_lstar": np.log(d.loc[y, c("LMEMPSTRL")] / d.loc[yp, c("LMEMPSTRL")])},
                coef["LMEMPTOTL"])
            d.loc[y, c("LMUNRTOTL_")] = (1 - d.loc[y, c("LMEMPTOTL")] / d.loc[y, c("LMLBFTOTL")]) * 100

            # ==============================================================
            # Fiscal with hydrocarbon erosion + fuel-subsidy block
            # ==============================================================
            # Revenue: ECM-based evolution pinned to nominal GDP
            d.loc[y, c("GGREVTOTLCN")] = apply_ecm(
                d.loc[yp, c("GGREVTOTLCN")], d.loc[yp, c("NYGDPMKTPCN")],
                {"dly_gdpn": dly_ngdp}, coef["GGREVTOTLCN"])
            d.loc[y, c("GGREVTAXTCN")] = apply_ecm(
                d.loc[yp, c("GGREVTAXTCN")], d.loc[yp, c("NYGDPMKTPCN")],
                {"dly_gdpn": dly_ngdp}, coef["GGREVTAXTCN"])
            d.loc[y, c("GGREVHYDRCN")] = apply_ecm(
                d.loc[yp, c("GGREVHYDRCN")], d.loc[yp, c("NYGDPMKTPCN")] * 0.1,
                {"dly_gdpn": dly_ngdp}, coef["GGREVHYDRCN"])
            # Expenditure: ECM + fuel-subsidy extra
            exp_base = apply_ecm(
                d.loc[yp, c("GGEXPTOTLCN")], d.loc[yp, c("NYGDPMKTPCN")],
                {"dly_gdpn": dly_ngdp}, coef["GGEXPTOTLCN"])
            fuel_extra = d.loc[y, c("FUEL_SUB_EXTRA")] * d.loc[y, c("NYGDPMKTPCN")]
            d.loc[y, c("GGEXPTOTLCN")] = exp_base + fuel_extra
            # Interest on prior-period debt at historical effective rate
            int_rate = d.loc[2024, c("GGEXPINTPCN")] / d.loc[2023, c("GGDBTTOTLCN")]
            d.loc[y, c("GGEXPINTPCN")] = int_rate * d.loc[yp, c("GGDBTTOTLCN")]
            # Balances
            d.loc[y, c("GGBALOVRLCN")] = d.loc[y, c("GGREVTOTLCN")] - d.loc[y, c("GGEXPTOTLCN")]
            d.loc[y, c("GGBALPRIMCN")] = (d.loc[y, c("GGREVTOTLCN")] -
                                          (d.loc[y, c("GGEXPTOTLCN")] - d.loc[y, c("GGEXPINTPCN")]))
            # Debt dynamics (NFPS perimeter)
            d.loc[y, c("GGDBTTOTLCN")] = d.loc[yp, c("GGDBTTOTLCN")] - d.loc[y, c("GGBALOVRLCN")]
            d.loc[y, c("GGDBTTOTLGD")] = d.loc[y, c("GGDBTTOTLCN")] / d.loc[y, c("NYGDPMKTPCN")] * 100
            d.loc[y, c("GGBALOVRLGD")] = d.loc[y, c("GGBALOVRLCN")] / d.loc[y, c("NYGDPMKTPCN")] * 100

            # BCB financing: residual = deficit less external financing less domestic private
            # Assume external net ~0 (IMF shows negative for 2025+) and private domestic ~3% GDP
            ext_net_gdp = -0.005  # small external amortization
            priv_dom_gdp = 0.005
            bcb_fin_gdp_new = -d.loc[y, c("GGBALOVRLGD")] - ext_net_gdp - priv_dom_gdp
            d.loc[y, c("GGFINBCBGD")] = bcb_fin_gdp_new
            d.loc[y, c("GGFINBCBCN")] = bcb_fin_gdp_new / 100 * d.loc[y, c("NYGDPMKTPCN")]

            # Reserves update (exogenous forecast already set)
            imp_usd_monthly = d.loc[y, c("NEIMPGNFSCN")] / d.loc[y, c("PANUSATLS")] / 12
            d.loc[y, c("FIRESMONTHS")] = d.loc[y, c("FIRESGRSCD")] * 1e6 / imp_usd_monthly

            # BoP
            d.loc[y, c("NYGDPMKTPCD")] = d.loc[y, c("NYGDPMKTPCN")] / d.loc[y, c("PANUSATLS")]
            d.loc[y, c("BXGSRMRCHCD")] = (d.loc[y, c("NEEXPGNFSCN")] / d.loc[y, c("PANUSATLS")]) * \
                (d.loc[2024, c("BXGSRMRCHCD")] * d.loc[2024, c("PANUSATLS")] / d.loc[2024, c("NEEXPGNFSCN")])
            d.loc[y, c("BMGSRMRCHCD")] = (d.loc[y, c("NEIMPGNFSCN")] / d.loc[y, c("PANUSATLS")]) * \
                (d.loc[2024, c("BMGSRMRCHCD")] * d.loc[2024, c("PANUSATLS")] / d.loc[2024, c("NEIMPGNFSCN")])
            d.loc[y, c("BXFSTREMTCD")] = d.loc[yp, c("BXFSTREMTCD")] * \
                (d.loc[y, c("XMKT_USD")] / d.loc[yp, c("XMKT_USD")])
            trade_bal = d.loc[y, c("BXGSRMRCHCD")] - d.loc[y, c("BMGSRMRCHCD")]
            other_cab_gdp = (d.loc[2024, c("BNCABFUNDCD")] - (d.loc[2024, c("BXGSRMRCHCD")] -
                            d.loc[2024, c("BMGSRMRCHCD")])) / d.loc[2024, c("NYGDPMKTPCD")]
            d.loc[y, c("BNCABFUNDCD")] = trade_bal + other_cab_gdp * d.loc[y, c("NYGDPMKTPCD")]

            # Convergence check
            key = [c("NYGDPMKTPKN"), c("FPCPITOTLXN"), c("GGBALOVRLCN"), c("GGDBTTOTLCN")]
            cur = d.loc[y, key].astype(float)
            old = prev_state[key].astype(float)
            if old.isna().any() or (old == 0).any():
                diff = np.inf
                continue
            diff = ((cur - old) / old).abs().max()
            if diff < TOL:
                print(f"  Converged in {it+1} iter (diff {diff:.2e})")
                break
        else:
            print(f"  WARN: no convergence (diff {diff:.2e})")

        print(f"  Real GDP growth  = {100*(np.exp(dly_gdp) - 1):.2f}%")
        print(f"  CPI inflation    = {100*pi_t:.2f}%")
        print(f"  Fiscal bal % GDP = {d.loc[y, c('GGBALOVRLGD')]:.2f}%")
        print(f"  NFPS Debt % GDP  = {d.loc[y, c('GGDBTTOTLGD')]:.2f}%")
        print(f"  BCB fin % GDP    = {d.loc[y, c('GGFINBCBGD')]:.2f}%")
        print(f"  Current acc USDm = {d.loc[y, c('BNCABFUNDCD')]/1e6:.0f}")

    # Save full solution
    d.to_csv(OUT)

    # Summary + IMF comparison
    imf_art_iv = {
        "RealGDP_g":    {2023:3.1, 2024:1.3, 2025:1.1, 2026:0.9, 2027:0.6},
        "CPI_avg":      {2023:2.6, 2024:5.1, 2025:15.1, 2026:15.8, 2027:17.1},
        "FiscBal_GDP":  {2023:-10.9, 2024:-10.3, 2025:-12.7, 2026:-13.2, 2027:-12.5},
        "NFPSDebt_GDP": {2023:90.8, 2024:95.0, 2025:90.4, 2026:91.4, 2027:92.8},
        "CA_GDP":       {2023:-2.5, 2024:-2.7, 2025:-2.6, 2026:-3.2, 2027:-3.8},
        "NomGDP_USDbn": {2023:45.5, 2024:48.4, 2025:56.3, 2026:65.9, 2027:75.0},
    }
    rows = []
    for y in range(2023, 2028):
        yp = y - 1
        rg = 100*(d.loc[y,c("NYGDPMKTPKN")]/d.loc[yp,c("NYGDPMKTPKN")] - 1)
        pi = 100*(d.loc[y,c("FPCPITOTLXN")]/d.loc[yp,c("FPCPITOTLXN")] - 1)
        row = {
            "year": y,
            "IMF_RealGDP":   imf_art_iv["RealGDP_g"].get(y),
            "v2_RealGDP":    rg,
            "IMF_CPI":       imf_art_iv["CPI_avg"].get(y),
            "v2_CPI":        pi,
            "IMF_FiscBal":   imf_art_iv["FiscBal_GDP"].get(y),
            "v2_FiscBal":    d.loc[y, c("GGBALOVRLGD")],
            "IMF_NFPSDebt":  imf_art_iv["NFPSDebt_GDP"].get(y),
            "v2_NFPSDebt":   d.loc[y, c("GGDBTTOTLGD")],
            "IMF_CA":        imf_art_iv["CA_GDP"].get(y),
            "v2_CA":         d.loc[y, c("BNCABFUNDCD")] / d.loc[y, c("NYGDPMKTPCD")] * 100,
            "IMF_NomGDP_USDbn": imf_art_iv["NomGDP_USDbn"].get(y),
            "v2_NomGDP_USDbn":  d.loc[y, c("NYGDPMKTPCD")] / 1e9,
        }
        rows.append(row)
    cmp = pd.DataFrame(rows).set_index("year").round(2)
    cmp.to_csv(CMP)
    print("\n" + "=" * 80)
    print("MFMod-BOL v2 vs IMF Art IV 2025")
    print("=" * 80)
    print(cmp.T.to_string())

if __name__ == "__main__":
    main()
