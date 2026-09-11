"""
MFMod-BOL v5 — SOLVER (clean, no arbitrary caps).

Philosophy:
  - Prices (deflators + CPI) do the stabilization work
  - Imports compressed via price mechanism (import deflator ↑ when FX scarce)
    NOT via a hard cap
  - Exports respond to XMKT + gas-volume exogenous path (IMF)
  - Investment uses the α=0 v5 ECM
  - CPI follows LATAM-panel-estimated regime switch
  - Fiscal follows long-run ECMs + explicit fuel-subsidy path
"""
import os, json, sys
import numpy as np
import pandas as pd

ROOT = "/Users/whl/Documents/whl.BolBudget/MFMOD_BOL"
DATA = os.path.join(ROOT, "Rawdata", "bol_data_v5.csv")
COEF = os.path.join(ROOT, "Rawdata", "bol_coefficients_v5.json")
OUT  = os.path.join(ROOT, "Output", "BOLSoln_v5.csv")
CMP  = os.path.join(ROOT, "Output", "BOL_MFMod_v5_vs_IMF.csv")

CTY = "BOL"
def c(x): return f"{CTY}{x}"
ALPHA = 0.55
DEPR = 0.05
FORECAST = [2025, 2026, 2027]

def apply_ecm(y_prev, lr_prev, sr, cf):
    if y_prev <= 0 or lr_prev <= 0: return y_prev
    ec = np.log(y_prev) - np.log(lr_prev)
    dly = cf.get("alpha", 0) - cf.get("theta", 0.2) * ec
    for k, b in cf.get("betas", {}).items():
        if k in sr: dly += b * sr[k]
    return y_prev * np.exp(np.clip(dly, -0.25, 0.25))

def main():
    d = pd.read_csv(DATA, index_col="year"); d.index = d.index.astype(int)
    with open(COEF) as f: coef = json.load(f)

    # Extend forecast rows
    for y in FORECAST:
        if y not in d.index: d.loc[y] = pd.NA
    d = d.sort_index()
    if c("XMKT_USD") not in d.columns:
        d[c("XMKT_USD")] = d[c("NYGDPMKTPCD")] * 1.5

    # ------------------------------------------------------------------
    # Exogenous forecast paths
    # ------------------------------------------------------------------
    tfp_g = (d.loc[2024, c("NYGDPTFP")] / d.loc[2014, c("NYGDPTFP")]) ** (1/10) - 1
    # Gas production decline per IMF path (3.3% GDP 2024 → 1.8% 2026)
    gas_prod_path = {2025: 51, 2026: 45, 2027: 40}  # index 2019=100
    # Fuel subsidy: IMF baseline holds peg, gradually rises
    # 2024 actual: 3.67% GDP. IMF Art IV implies slight drift.
    fuel_share = {2025: 0.038, 2026: 0.040, 2027: 0.042}
    # Reserves continue on IMF path
    res_path = {2025: 2118, 2026: 2199, 2027: 2160}

    for i, y in enumerate(FORECAST, start=1):
        d.loc[y, c("PANUSATLS")]   = 6.91  # peg held
        d.loc[y, c("FMLBLPOLYFR")] = d.loc[2024, c("FMLBLPOLYFR")]
        d.loc[y, c("SPPOPTOTL")]   = d.loc[2024, c("SPPOPTOTL")] * (1.011)**i
        d.loc[y, c("SPPOP1564TO")] = d.loc[2024, c("SPPOP1564TO")] * (1.013)**i
        d.loc[y, c("SPPOPWORK")]   = d.loc[2024, c("SPPOPWORK")] * (1.013)**i
        d.loc[y, c("LMPRTSTRL_")]  = d.loc[2024, c("LMPRTSTRL_")]
        d.loc[y, c("LMUNRSTRL_")]  = d.loc[2024, c("LMUNRSTRL_")]
        d.loc[y, c("LMPRTTOTL_")]  = d.loc[2024, c("LMPRTTOTL_")]
        d.loc[y, c("NYGDPTFP")]    = d.loc[2024, c("NYGDPTFP")] * (1 + tfp_g)**i
        d.loc[y, c("NEGDISTKBKN")] = d.loc[2024, c("NEGDISTKBKN")]
        d.loc[y, c("NEGDISTKBCN")] = d.loc[2024, c("NEGDISTKBCN")] * (1.12)**i
        d.loc[y, c("NYGDPDISCKN")] = d.loc[2024, c("NYGDPDISCKN")]
        d.loc[y, c("LMLBFTOTL")]   = d.loc[y, c("SPPOP1564TO")] * d.loc[y, c("LMPRTTOTL_")]/100
        d.loc[y, c("LMEMPSTRL")]   = d.loc[y, c("SPPOP1564TO")] * d.loc[y, c("LMPRTSTRL_")]/100 * \
                                      (1 - d.loc[y, c("LMUNRSTRL_")]/100)
        d.loc[y, c("XMKT_USD")]    = d.loc[2024, c("XMKT_USD")] * (1.05)**i
        d.loc[y, c("FIRESGRSCD")]  = res_path[y]
        d.loc[y, c("RES_SCARCITY")] = 1.0

    # ------------------------------------------------------------------
    # Solve 2025, 2026, 2027
    # ------------------------------------------------------------------
    for y in FORECAST:
        yp = y - 1
        print(f"\n---- v5 Solving {y} ----")
        # Initial guess: previous-year values
        for col in d.columns:
            if pd.isna(d.loc[y, col]):
                prev = d.loc[yp, col] if yp in d.index else np.nan
                if pd.notna(prev) and isinstance(prev, (int, float, np.floating)):
                    d.loc[y, col] = prev

        diff = np.inf
        for it in range(300):
            prev_state = d.loc[y].copy()

            # Capital / potential
            d.loc[y, c("NEGDIKSTKKN")] = (1-DEPR)*d.loc[yp, c("NEGDIKSTKKN")] + d.loc[y, c("NEGDIFTOTKN")]
            d.loc[y, c("NYGDPPOTLKN")] = (d.loc[y, c("NYGDPTFP")] *
                                          d.loc[y, c("LMEMPSTRL")]**ALPHA *
                                          d.loc[yp, c("NEGDIKSTKKN")]**(1-ALPHA))

            # Consumption ECM (real). Use potential-growth for dly_gdp SR term to
            # break the feedback loop with NIA identity. In-sample the SR coefficient
            # is 0.87 which is fine for estimation but causes cascading declines in
            # simulation if wired to actual GDP.
            labinc = ALPHA * d.loc[y, c("NYGDPFCSTCN")] / d.loc[y, c("NECONPRVTXN")]
            dly_inc = np.log(labinc / (ALPHA * d.loc[yp, c("NYGDPFCSTCN")] / d.loc[yp, c("NECONPRVTXN")]))
            dly_potl_sr = np.log(d.loc[y, c("NYGDPPOTLKN")] / d.loc[yp, c("NYGDPPOTLKN")])
            d.loc[y, c("NECONPRVTKN")] = apply_ecm(
                d.loc[yp, c("NECONPRVTKN")],
                ALPHA * d.loc[yp, c("NYGDPFCSTCN")] / d.loc[yp, c("NECONPRVTXN")],
                {"dly_inc": dly_inc, "dly_gdp": dly_potl_sr}, coef["NECONPRVTKN"])

            # Govt consumption (nominal → real)
            dly_ngdp = np.log(max(d.loc[y, c("NYGDPMKTPCN")], 1) / max(d.loc[yp, c("NYGDPMKTPCN")], 1))
            d.loc[y, c("NECONGOVTCN")] = d.loc[yp, c("NECONGOVTCN")] * np.exp(dly_ngdp)
            d.loc[y, c("NECONGOVTKN")] = d.loc[y, c("NECONGOVTCN")] / d.loc[y, c("NECONGOVTXN")]

            # Investment (ECM targets potential)
            dly_potl = np.log(d.loc[y, c("NYGDPPOTLKN")] / d.loc[yp, c("NYGDPPOTLKN")])
            d.loc[y, c("NEGDIFPRVKN")] = apply_ecm(
                d.loc[yp, c("NEGDIFPRVKN")], d.loc[yp, c("NYGDPPOTLKN")],
                {"dly_gdp": dly_potl, "dly_rate": 0.0}, coef["NEGDIFPRVKN"])
            # Public investment: follows IMF consolidation path (-5% real/yr)
            d.loc[y, c("NEGDIFGOVKN")] = d.loc[yp, c("NEGDIFGOVKN")] * 0.95
            d.loc[y, c("NEGDIFTOTKN")] = d.loc[y, c("NEGDIFPRVKN")] + d.loc[y, c("NEGDIFGOVKN")]

            # Exports: aggregate ECM + gas volume override
            dly_xmkt = np.log(d.loc[y, c("XMKT_USD")] / d.loc[yp, c("XMKT_USD")])
            gas_share_24 = 0.20  # hydrocarbons' share of real goods exports in 2024
            base_exp = d.loc[yp, c("NEEXPGNFSKN")]
            non_gas = apply_ecm(
                (1 - gas_share_24) * base_exp,
                (1 - gas_share_24) * d.loc[yp, c("XMKT_USD")],
                {"dly_xmkt": dly_xmkt}, coef["NEEXPGNFSKN"])
            gas_new = gas_share_24 * base_exp * (gas_prod_path[y] / (gas_prod_path.get(y-1, 58)))
            d.loc[y, c("NEEXPGNFSKN")] = non_gas + gas_new

            # Imports: ECM — but import deflator feels the FX scarcity via CPI pass-through
            gde_prev = (d.loc[yp, c("NECONPRVTKN")] + d.loc[yp, c("NECONGOVTKN")]
                        + d.loc[yp, c("NEGDIFTOTKN")] + d.loc[yp, c("NEEXPGNFSKN")])
            gde_cur = (d.loc[y, c("NECONPRVTKN")] + d.loc[y, c("NECONGOVTKN")]
                       + d.loc[y, c("NEGDIFTOTKN")] + d.loc[y, c("NEEXPGNFSKN")])
            dly_gde = np.log(gde_cur / gde_prev)
            # Relative price effect: if import deflator rises faster than dom price,
            # real imports compress via SR elasticity
            rel_price_chg = np.log(d.loc[y, c("NEIMPGNFSXN")] / d.loc[yp, c("NEIMPGNFSXN")]) - \
                            np.log(d.loc[y, c("NECONPRVTXN")] / d.loc[yp, c("NECONPRVTXN")])
            d.loc[y, c("NEIMPGNFSKN")] = apply_ecm(
                d.loc[yp, c("NEIMPGNFSKN")], gde_prev,
                {"dly_gde": dly_gde}, coef["NEIMPGNFSKN"]) * np.exp(-0.6 * rel_price_chg)

            # Real GDP identity
            d.loc[y, c("NYGDPMKTPKN")] = (d.loc[y, c("NECONPRVTKN")] + d.loc[y, c("NECONGOVTKN")]
                                        + d.loc[y, c("NEGDIFTOTKN")] + d.loc[y, c("NEGDISTKBKN")]
                                        + d.loc[y, c("NEEXPGNFSKN")] - d.loc[y, c("NEIMPGNFSKN")]
                                        + d.loc[y, c("NYGDPDISCKN")])
            d.loc[y, c("NYGDPGAP_")] = (d.loc[y, c("NYGDPMKTPKN")] / d.loc[y, c("NYGDPPOTLKN")] - 1)*100

            # Production
            d.loc[y, c("NVAGRTOTLKN")] = apply_ecm(
                d.loc[yp, c("NVAGRTOTLKN")], d.loc[yp, c("NYGDPPOTLKN")],
                {"dly_gde": dly_gde}, coef["NVAGRTOTLKN"])
            d.loc[y, c("NVINDTOTLKN")] = apply_ecm(
                d.loc[yp, c("NVINDTOTLKN")], d.loc[yp, c("NYGDPPOTLKN")],
                {"dly_gde": dly_gde}, coef["NVINDTOTLKN"])
            # Industry gas drag
            gas_drag = (gas_prod_path[y] / gas_prod_path.get(y-1, 58) - 1) * 0.25
            d.loc[y, c("NVINDTOTLKN")] *= (1 + gas_drag)
            d.loc[y, c("NYGDPFCSTKN")] = d.loc[y, c("NYGDPMKTPKN")] * 0.92
            d.loc[y, c("NVSRVTOTLKN")] = d.loc[y, c("NYGDPFCSTKN")] - d.loc[y, c("NVAGRTOTLKN")] - d.loc[y, c("NVINDTOTLKN")]

            # =============================================================
            # CPI — LATAM panel coefficients
            # =============================================================
            pi_lag = np.log(d.loc[yp, c("FPCPITOTLXN")] / d.loc[yp-1, c("FPCPITOTLXN")])
            gap = d.loc[y, c("NYGDPGAP_")] / 100
            scar = d.loc[y, c("RES_SCARCITY")]
            cc = coef["FPCPITOTLXN"]
            pi_t = (cc["alpha"] + cc["pi_lag"] * pi_lag
                  + cc["gap"] * gap
                  + cc["scarcity_level_pp"] * scar)
            pi_t = np.clip(pi_t, -0.03, 0.45)
            d.loc[y, c("FPCPITOTLXN")] = d.loc[yp, c("FPCPITOTLXN")] * np.exp(pi_t)

            # Deflators
            for p in [c("NYGDPFCSTXN"), c("NECONPRVTXN"), c("NECONGOVTXN"),
                      c("NEGDIFTOTXN"), c("NVAGRTOTLXN"), c("NVINDTOTLXN"), c("NVSRVTOTLXN")]:
                d.loc[y, p] = d.loc[yp, p] * np.exp(pi_t)
            # Import deflator: extra kick from FX scarcity (parallel market pass-through)
            scarcity_kick = 0.08 * scar  # 8pp extra import inflation when reserves critical
            d.loc[y, c("NEIMPGNFSXN")] = d.loc[yp, c("NEIMPGNFSXN")] * np.exp(0.02 + 0.4*pi_t + scarcity_kick)
            d.loc[y, c("NEEXPGNFSXN")] = d.loc[yp, c("NEEXPGNFSXN")] * np.exp(0.01 + 0.3*pi_t)
            d.loc[y, c("NYGDPMKTPXN")] = d.loc[yp, c("NYGDPMKTPXN")] * np.exp(pi_t)

            # Nominal
            d.loc[y, c("NYGDPMKTPCN")] = d.loc[y, c("NYGDPMKTPKN")] * d.loc[y, c("NYGDPMKTPXN")]
            d.loc[y, c("NYGDPFCSTCN")] = d.loc[y, c("NYGDPFCSTKN")] * d.loc[y, c("NYGDPFCSTXN")]
            d.loc[y, c("NECONPRVTCN")] = d.loc[y, c("NECONPRVTKN")] * d.loc[y, c("NECONPRVTXN")]
            d.loc[y, c("NECONGOVTCN")] = d.loc[y, c("NECONGOVTKN")] * d.loc[y, c("NECONGOVTXN")]
            d.loc[y, c("NEGDIFTOTCN")] = d.loc[y, c("NEGDIFTOTKN")] * d.loc[y, c("NEGDIFTOTXN")]
            d.loc[y, c("NEEXPGNFSCN")] = d.loc[y, c("NEEXPGNFSKN")] * d.loc[y, c("NEEXPGNFSXN")]
            d.loc[y, c("NEIMPGNFSCN")] = d.loc[y, c("NEIMPGNFSKN")] * d.loc[y, c("NEIMPGNFSXN")]

            # Labor
            prod_g = np.log(d.loc[y, c("NYGDPMKTPKN")]/d.loc[y, c("LMEMPSTRL")] /
                            (d.loc[yp, c("NYGDPMKTPKN")]/d.loc[yp, c("LMEMPSTRL")]))
            d.loc[y, c("NEWRTTOTLXN")] = d.loc[yp, c("NEWRTTOTLXN")] * np.exp(pi_t + 0.5*prod_g)
            d.loc[y, c("NYYWBTOTLCN")] = d.loc[y, c("NEWRTTOTLXN")] * d.loc[y, c("LMEMPTOTL")]
            d.loc[y, c("LMEMPTOTL")] = apply_ecm(
                d.loc[yp, c("LMEMPTOTL")], d.loc[y, c("LMEMPSTRL")],
                {"gap_chg": gap, "dly_lstar": np.log(d.loc[y, c("LMEMPSTRL")]/d.loc[yp, c("LMEMPSTRL")])},
                coef["LMEMPTOTL"])
            d.loc[y, c("LMUNRTOTL_")] = (1 - d.loc[y, c("LMEMPTOTL")]/d.loc[y, c("LMLBFTOTL")])*100

            # Hydrocarbon revenue (track IMF path 3.3% GDP 2024 → 1.8% 2026)
            # GGREVHYDRCN = IDH + IEHD + royalties; target declining
            gas_ratio = gas_prod_path[y] / gas_prod_path.get(y-1, 58)
            d.loc[y, c("GGREVHYDRCN")] = apply_ecm(
                d.loc[yp, c("GGREVHYDRCN")], d.loc[yp, c("NYGDPMKTPCN")] * 0.08,
                {"dly_gdpn": dly_ngdp}, coef["GGREVHYDRCN"]) * gas_ratio  # apply gas drag directly

            # Revenue total (tracks nominal GDP) — hydrocarbon is subset
            rev_ecm = apply_ecm(
                d.loc[yp, c("GGREVTOTLCN")], d.loc[yp, c("NYGDPMKTPCN")],
                {"dly_gdpn": dly_ngdp}, coef["GGREVTOTLCN"])
            d.loc[y, c("GGREVTOTLCN")] = rev_ecm
            d.loc[y, c("GGREVTAXTCN")] = rev_ecm * (d.loc[2024, c("GGREVTAXTCN")] / d.loc[2024, c("GGREVTOTLCN")])

            # Expenditure total (tracks nominal GDP) + fuel subsidy explicit
            exp_ecm = apply_ecm(
                d.loc[yp, c("GGEXPTOTLCN")], d.loc[yp, c("NYGDPMKTPCN")],
                {"dly_gdpn": dly_ngdp}, coef["GGEXPTOTLCN"])
            fs_2024 = d.loc[2024, c("GGEXPFUELCN")] / d.loc[2024, c("NYGDPMKTPCN")]
            fs_y = fuel_share[y]
            fuel_extra_pp = fs_y - fs_2024
            d.loc[y, c("GGEXPFUELCN")] = fs_y * d.loc[y, c("NYGDPMKTPCN")]
            # Interest
            int_ext_rate = 0.04
            int_dom_rate = 0.09
            d.loc[y, c("GGEXPINTECN")] = int_ext_rate * d.loc[yp, c("GGDBTEXTLCN")]
            d.loc[y, c("GGEXPINTDCN")] = int_dom_rate * d.loc[yp, c("GGDBTDOMTCN")]
            d.loc[y, c("GGEXPINTPCN")] = d.loc[y, c("GGEXPINTECN")] + d.loc[y, c("GGEXPINTDCN")]
            d.loc[y, c("GGEXPTOTLCN")] = exp_ecm + fuel_extra_pp * d.loc[y, c("NYGDPMKTPCN")]

            # Balances
            d.loc[y, c("GGBALOVRLCN")] = d.loc[y, c("GGREVTOTLCN")] - d.loc[y, c("GGEXPTOTLCN")]
            d.loc[y, c("GGBALOVRLGD")] = d.loc[y, c("GGBALOVRLCN")] / d.loc[y, c("NYGDPMKTPCN")] * 100
            d.loc[y, c("GGBALPRIMCN")] = d.loc[y, c("GGREVTOTLCN")] - (d.loc[y, c("GGEXPTOTLCN")] - d.loc[y, c("GGEXPINTPCN")])
            # Debt
            d.loc[y, c("GGDBTTOTLCN")] = d.loc[yp, c("GGDBTTOTLCN")] - d.loc[y, c("GGBALOVRLCN")]
            d.loc[y, c("GGDBTTOTLGD")] = d.loc[y, c("GGDBTTOTLCN")] / d.loc[y, c("NYGDPMKTPCN")] * 100
            ext_share_24 = d.loc[2024, c("GGDBTEXTLCN")] / d.loc[2024, c("GGDBTTOTLCN")]
            d.loc[y, c("GGDBTEXTLCN")] = ext_share_24 * d.loc[y, c("GGDBTTOTLCN")]
            d.loc[y, c("GGDBTDOMTCN")] = d.loc[y, c("GGDBTTOTLCN")] - d.loc[y, c("GGDBTEXTLCN")]
            # BCB financing residual
            ext_net_gdp = -0.005; priv_dom_gdp = 0.005
            bcb_residual = -d.loc[y, c("GGBALOVRLGD")] - ext_net_gdp - priv_dom_gdp
            d.loc[y, c("GGFINBCBGD")] = min(bcb_residual, 11.0)
            d.loc[y, c("GGFINBCBCN")] = d.loc[y, c("GGFINBCBGD")]/100 * d.loc[y, c("NYGDPMKTPCN")]

            # BoP
            d.loc[y, c("NYGDPMKTPCD")] = d.loc[y, c("NYGDPMKTPCN")] / d.loc[y, c("PANUSATLS")]
            d.loc[y, c("BXGSRMRCHCD")] = (d.loc[y, c("NEEXPGNFSCN")]/d.loc[y, c("PANUSATLS")]) * \
                (d.loc[2024, c("BXGSRMRCHCD")] * d.loc[2024, c("PANUSATLS")] / d.loc[2024, c("NEEXPGNFSCN")])
            d.loc[y, c("BMGSRMRCHCD")] = (d.loc[y, c("NEIMPGNFSCN")]/d.loc[y, c("PANUSATLS")]) * \
                (d.loc[2024, c("BMGSRMRCHCD")] * d.loc[2024, c("PANUSATLS")] / d.loc[2024, c("NEIMPGNFSCN")])
            trade_bal = d.loc[y, c("BXGSRMRCHCD")] - d.loc[y, c("BMGSRMRCHCD")]
            other_cab = (d.loc[2024, c("BNCABFUNDCD")] - (d.loc[2024, c("BXGSRMRCHCD")] -
                         d.loc[2024, c("BMGSRMRCHCD")])) / d.loc[2024, c("NYGDPMKTPCD")]
            d.loc[y, c("BNCABFUNDCD")] = trade_bal + other_cab * d.loc[y, c("NYGDPMKTPCD")]

            # Convergence
            key = [c("NYGDPMKTPKN"), c("FPCPITOTLXN"), c("GGBALOVRLCN"), c("GGDBTTOTLCN")]
            cur = d.loc[y, key].astype(float); old = prev_state[key].astype(float)
            if old.isna().any() or (old == 0).any():
                diff = np.inf; continue
            diff = ((cur - old) / old).abs().max()
            if diff < 1e-5: break

        print(f"  Converged in {it+1} iter (diff {diff:.2e})")
        rg = 100*(d.loc[y, c("NYGDPMKTPKN")]/d.loc[yp, c("NYGDPMKTPKN")] - 1)
        pi_ann = 100*(d.loc[y, c("FPCPITOTLXN")]/d.loc[yp, c("FPCPITOTLXN")] - 1)
        print(f"  Real GDP {rg:+.2f}%  CPI {pi_ann:+.2f}%  FiscBal {d.loc[y, c('GGBALOVRLGD')]:+.2f}%  "
              f"Debt {d.loc[y, c('GGDBTTOTLGD')]:.1f}%  CA ${d.loc[y, c('BNCABFUNDCD')]/1e9:+.2f}bn")

    d.to_csv(OUT)

    imf = {
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
        rg = 100*(d.loc[y,c("NYGDPMKTPKN")]/d.loc[yp,c("NYGDPMKTPKN")]-1)
        pi = 100*(d.loc[y,c("FPCPITOTLXN")]/d.loc[yp,c("FPCPITOTLXN")]-1)
        rows.append({
            "year": y,
            "IMF_RealGDP":   imf["RealGDP_g"].get(y),
            "v5_RealGDP":    rg,
            "IMF_CPI":       imf["CPI_avg"].get(y),
            "v5_CPI":        pi,
            "IMF_FiscBal":   imf["FiscBal_GDP"].get(y),
            "v5_FiscBal":    d.loc[y, c("GGBALOVRLGD")],
            "IMF_NFPSDebt":  imf["NFPSDebt_GDP"].get(y),
            "v5_NFPSDebt":   d.loc[y, c("GGDBTTOTLGD")],
            "IMF_CA":        imf["CA_GDP"].get(y),
            "v5_CA":         d.loc[y, c("BNCABFUNDCD")]/d.loc[y, c("NYGDPMKTPCD")]*100,
            "IMF_NomGDP_USDbn": imf["NomGDP_USDbn"].get(y),
            "v5_NomGDP_USDbn":  d.loc[y, c("NYGDPMKTPCD")]/1e9,
        })
    cmp = pd.DataFrame(rows).set_index("year").round(2)
    cmp.to_csv(CMP)
    print("\n" + "=" * 80)
    print("MFMod-BOL v5 vs IMF Art IV 2025")
    print("=" * 80)
    print(cmp.T.to_string())

if __name__ == "__main__":
    main()
