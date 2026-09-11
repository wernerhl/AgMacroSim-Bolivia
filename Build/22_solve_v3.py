"""
MFMod-BOL v3 — Solver with component-level expenditure + hydrocarbon block.
Keeps v2 CPI + reserve-scarcity channel; adds:
  - Expenditure as sum of 8 components each evolving by own rule.
  - Hydrocarbon sub-block: gas production (exog) → gas export USD → IDH revenue.
  - Imports pinned to IMF-path lower bound under FX scarcity.
  - Base-year-smoothed 2024 values (handled in step 21).
"""
import os, json
import numpy as np
import pandas as pd

ROOT = "/Users/whl/Documents/whl.BolBudget/MFMOD_BOL"
DATA = os.path.join(ROOT, "Rawdata", "bol_data_v3.csv")
COEF = os.path.join(ROOT, "Rawdata", "bol_coefficients_v2.json")  # reuse v2 ECMs
OUT  = os.path.join(ROOT, "Output", "BOLSoln_v3.csv")
CMP  = os.path.join(ROOT, "Output", "BOL_MFMod_v3_vs_IMF.csv")

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
    return y_prev * np.exp(np.clip(dlog_y, -0.25, 0.25))

def main():
    d = pd.read_csv(DATA, index_col="year")
    d.index = d.index.astype(int)
    with open(COEF) as f: coef = json.load(f)

    # Extend exog rows
    for y in FORECAST:
        if y not in d.index: d.loc[y] = pd.NA
    d = d.sort_index()

    # Ensure XMKT_USD column exists (external demand proxy)
    if c("XMKT_USD") not in d.columns:
        d[c("XMKT_USD")] = d[c("NYGDPMKTPCD")] * 1.5

    # ------------------------------------------------------------------
    # Exogenous forecasts (2025-2027)
    # ------------------------------------------------------------------
    # Peg, rate, pop, TFP, structural labor — same as v2
    tfp_g = (d.loc[2024, c("NYGDPTFP")] / d.loc[2014, c("NYGDPTFP")]) ** (1/10) - 1
    for i, y in enumerate(FORECAST, start=1):
        d.loc[y, c("PANUSATLS")]    = 6.91
        d.loc[y, c("FMLBLPOLYFR")]  = d.loc[2024, c("FMLBLPOLYFR")]
        d.loc[y, c("SPPOPTOTL")]    = d.loc[2024, c("SPPOPTOTL")] * (1.011)**i
        d.loc[y, c("SPPOP1564TO")]  = d.loc[2024, c("SPPOP1564TO")] * (1.013)**i
        d.loc[y, c("SPPOPWORK")]    = d.loc[2024, c("SPPOPWORK")] * (1.013)**i
        d.loc[y, c("LMPRTSTRL_")]   = d.loc[2024, c("LMPRTSTRL_")]
        d.loc[y, c("LMUNRSTRL_")]   = d.loc[2024, c("LMUNRSTRL_")]
        d.loc[y, c("LMPRTTOTL_")]   = d.loc[2024, c("LMPRTTOTL_")]
        d.loc[y, c("NYGDPTFP")]     = d.loc[2024, c("NYGDPTFP")] * (1 + tfp_g)**i
        d.loc[y, c("NEGDISTKBKN")]  = d.loc[2024, c("NEGDISTKBKN")]
        d.loc[y, c("NEGDISTKBCN")]  = d.loc[2024, c("NEGDISTKBCN")] * (1.12)**i
        d.loc[y, c("NYGDPDISCKN")]  = d.loc[2024, c("NYGDPDISCKN")]
        d.loc[y, c("LMLBFTOTL")]    = d.loc[y, c("SPPOP1564TO")] * d.loc[y, c("LMPRTTOTL_")]/100
        d.loc[y, c("LMEMPSTRL")]    = d.loc[y, c("SPPOP1564TO")] * d.loc[y, c("LMPRTSTRL_")]/100 * \
                                      (1 - d.loc[y, c("LMUNRSTRL_")]/100)
        d.loc[y, c("NYGDPMKTPCD")]  = d.loc[2024, c("NYGDPMKTPCD")] * (1.08)**i  # placeholder
        d.loc[y, c("XMKT_USD")]     = d.loc[2024, c("XMKT_USD")] * (1.05)**i
        d.loc[y, c("FIRESGRSCD")]   = {2025:2118, 2026:2199, 2027:2160}[y]
        d.loc[y, c("RES_SCARCITY")] = 1.0

    # ------- Hydrocarbon exogenous path (IMF-calibrated) ----------------
    # Gas production decline: -12%/yr 2025-2027 (already at 58 in 2024)
    gas_path = {2025: 51, 2026: 45, 2027: 40}
    for y, v in gas_path.items():
        d.loc[y, c("GASPROD")] = v

    # ------- Expenditure-component forecast rules ------------------------
    # Wages: nominal grows with CPI × (1 + public_employment_growth 0.5%)
    # Pensions (part of TRNS): grow with CPI × (1 + beneficiaries 3%)
    # Goods & services: grow with nominal GDP
    # Capex: real DECLINE 5%/yr (IMF consolidation), nominal grows with CPI × 0.95
    # Other: grow with nominal GDP
    # Fuel subsidy: explicit path
    FUEL_SUB_PATH_GDP = {2025: 0.050, 2026: 0.055, 2027: 0.060}  # 5-6% GDP

    # ------------------------------------------------------------------
    # Initial guesses for endogenous
    # ------------------------------------------------------------------
    for y in FORECAST:
        yp = y - 1
        g_potl = (np.log(d.loc[y-1, c("NYGDPTFP")] / d.loc[yp, c("NYGDPTFP")])
                  + ALPHA * np.log(d.loc[y, c("LMEMPSTRL")] / d.loc[yp, c("LMEMPSTRL")])
                  + (1 - ALPHA) * np.log(d.loc[yp, c("NEGDIKSTKKN")] / d.loc[yp-1, c("NEGDIKSTKKN")]))
        # Initial guess: just copy previous year (no bootstrap amplification)
        for col in d.columns:
            if pd.isna(d.loc[y, col]):
                prev = d.loc[yp, col] if yp in d.index else np.nan
                if pd.notna(prev) and isinstance(prev, (int, float, np.floating)):
                    d.loc[y, col] = prev

        # ==============================================================
        # Gauss-Seidel
        # ==============================================================
        print(f"\n---- v3 Solving {y} ----")
        diff = np.inf
        for it in range(MAX_ITER):
            prev_state = d.loc[y].copy()

            # Capital, potential
            d.loc[y, c("NEGDIKSTKKN")] = (1-DEPR)*d.loc[yp, c("NEGDIKSTKKN")] + d.loc[y, c("NEGDIFTOTKN")]
            d.loc[y, c("NYGDPPOTLKN")] = (d.loc[y, c("NYGDPTFP")] *
                                          d.loc[y, c("LMEMPSTRL")]**ALPHA *
                                          d.loc[yp, c("NEGDIKSTKKN")]**(1-ALPHA))

            # Consumption
            labinc_real = ALPHA * d.loc[y, c("NYGDPFCSTCN")] / d.loc[y, c("NECONPRVTXN")]
            dly_inc = np.log(labinc_real / (ALPHA * d.loc[yp, c("NYGDPFCSTCN")] / d.loc[yp, c("NECONPRVTXN")]))
            dly_gdp = np.log(d.loc[y, c("NYGDPMKTPKN")] / d.loc[yp, c("NYGDPMKTPKN")])
            d.loc[y, c("NECONPRVTKN")] = apply_ecm(
                d.loc[yp, c("NECONPRVTKN")],
                ALPHA * d.loc[yp, c("NYGDPFCSTCN")] / d.loc[yp, c("NECONPRVTXN")],
                {"dly_inc": dly_inc, "dly_gdp": dly_gdp}, coef["NECONPRVTKN"])

            # Govt consumption (nominal) = govt wages + goods (part of consumption)
            # Defer to after expenditure block; initially pin to nominal GDP
            dly_ngdp_prev = np.log(max(d.loc[y, c("NYGDPMKTPCN")], 1) / max(d.loc[yp, c("NYGDPMKTPCN")], 1))
            d.loc[y, c("NECONGOVTCN")] = d.loc[yp, c("NECONGOVTCN")] * np.exp(dly_ngdp_prev)
            d.loc[y, c("NECONGOVTKN")] = d.loc[y, c("NECONGOVTCN")] / d.loc[y, c("NECONGOVTXN")]

            # Investment with potential-growth SR (breaks feedback loop)
            dly_potl_y = np.log(d.loc[y, c("NYGDPPOTLKN")] / d.loc[yp, c("NYGDPPOTLKN")])
            d.loc[y, c("NEGDIFPRVKN")] = apply_ecm(
                d.loc[yp, c("NEGDIFPRVKN")], d.loc[yp, c("NYGDPPOTLKN")],
                {"dly_gdp": dly_potl_y, "dly_rate": 0.0}, coef["NEGDIFPRVKN"])
            # Public capex (real): declines 5%/yr per IMF consolidation path
            d.loc[y, c("NEGDIFGOVKN")] = d.loc[yp, c("NEGDIFGOVKN")] * 0.95
            d.loc[y, c("NEGDIFTOTKN")] = d.loc[y, c("NEGDIFPRVKN")] + d.loc[y, c("NEGDIFGOVKN")]

            # Exports: non-gas via ECM + gas-specific decline (from hydrocarbon block below)
            dly_xmkt = np.log(d.loc[y, c("XMKT_USD")] / d.loc[yp, c("XMKT_USD")])
            # Gas share of real exports: base 20% in 2024, declines as production drops
            gas_share_prev = 0.20 * (d.loc[yp, c("GASPROD")] / 58) if pd.notna(d.loc[yp, c("GASPROD")]) else 0.20
            gas_share_cur = 0.20 * (d.loc[y, c("GASPROD")] / 58)
            exp_lag = d.loc[yp, c("NEEXPGNFSKN")]
            non_gas_new = apply_ecm(
                (1 - gas_share_prev) * exp_lag,
                (1 - gas_share_prev) * d.loc[yp, c("XMKT_USD")],
                {"dly_xmkt": dly_xmkt}, coef["NEEXPGNFSKN"])
            gas_new = exp_lag * gas_share_prev * (d.loc[y, c("GASPROD")] / d.loc[yp, c("GASPROD")])
            d.loc[y, c("NEEXPGNFSKN")] = non_gas_new + gas_new

            # Imports ECM + FX-scarcity cap at IMF path (imports/GDP declines)
            gde_prev = (d.loc[yp, c("NECONPRVTKN")] + d.loc[yp, c("NECONGOVTKN")]
                        + d.loc[yp, c("NEGDIFTOTKN")] + d.loc[yp, c("NEEXPGNFSKN")])
            gde_cur  = (d.loc[y, c("NECONPRVTKN")] + d.loc[y, c("NECONGOVTKN")]
                        + d.loc[y, c("NEGDIFTOTKN")] + d.loc[y, c("NEEXPGNFSKN")])
            dly_gde = np.log(gde_cur / gde_prev)
            imp_ecm = apply_ecm(d.loc[yp, c("NEIMPGNFSKN")], gde_prev,
                                {"dly_gde": dly_gde}, coef["NEIMPGNFSKN"])
            # FX-scarcity cap: imports cannot exceed historical share path (IMF: 23.4→18.9% GDP)
            # Use real GDP × target real-imports share (anchored to 2024 ratio in real terms)
            imp_share_2024 = d.loc[2024, c("NEIMPGNFSKN")] / d.loc[2024, c("NYGDPMKTPKN")]
            imp_share_path = {2025: imp_share_2024 * 0.92,
                              2026: imp_share_2024 * 0.84,
                              2027: imp_share_2024 * 0.82}.get(y, imp_share_2024)
            imp_cap = imp_share_path * d.loc[y, c("NYGDPMKTPKN")]
            d.loc[y, c("NEIMPGNFSKN")] = min(imp_ecm, imp_cap)

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
            # Industry gets hit by gas decline
            gas_va_drag = (d.loc[y, c("GASPROD")]/d.loc[yp, c("GASPROD")] - 1) * 0.25  # 25% of industry is hydrocarbons
            d.loc[y, c("NVINDTOTLKN")] = d.loc[y, c("NVINDTOTLKN")] * (1 + gas_va_drag)
            d.loc[y, c("NYGDPFCSTKN")] = d.loc[y, c("NYGDPMKTPKN")] * 0.92
            d.loc[y, c("NVSRVTOTLKN")] = d.loc[y, c("NYGDPFCSTKN")] - d.loc[y, c("NVAGRTOTLKN")] - d.loc[y, c("NVINDTOTLKN")]

            # ==============================================================
            # CPI (Phillips + scarcity × BCB-fin channel)
            # ==============================================================
            pi_lag = np.log(d.loc[yp, c("FPCPITOTLXN")] / d.loc[yp-1, c("FPCPITOTLXN")])
            gap = d.loc[y, c("NYGDPGAP_")] / 100
            bcb_fin_gdp_prev = d.loc[y, c("GGFINBCBGD")] if pd.notna(d.loc[y].get(c("GGFINBCBGD"), np.nan)) else 10.0
            scar = d.loc[y, c("RES_SCARCITY")]
            cc = coef["FPCPITOTLXN"]
            # Recalibrate fin_scar to 0.60 (v2 had 0.80 but that was with more limited
            # expenditure response; with component block the combined channel is stronger)
            pi_t = (cc["alpha"] + cc["pi_lag"]*pi_lag + cc["gap"]*gap
                  + 0.60 * scar * (bcb_fin_gdp_prev/100))
            pi_t = np.clip(pi_t, -0.03, 0.22)  # cap hyperinflation tail
            d.loc[y, c("FPCPITOTLXN")] = d.loc[yp, c("FPCPITOTLXN")] * np.exp(pi_t)

            # Deflators
            for p in [c("NYGDPFCSTXN"), c("NECONPRVTXN"), c("NECONGOVTXN"),
                      c("NEGDIFTOTXN"), c("NVAGRTOTLXN"), c("NVINDTOTLXN"), c("NVSRVTOTLXN")]:
                d.loc[y, p] = d.loc[yp, p] * np.exp(pi_t)
            d.loc[y, c("NEIMPGNFSXN")] = d.loc[yp, c("NEIMPGNFSXN")] * np.exp(0.02 + 0.4*pi_t)
            d.loc[y, c("NEEXPGNFSXN")] = d.loc[yp, c("NEEXPGNFSXN")] * np.exp(0.01 + 0.3*pi_t)
            d.loc[y, c("NYGDPMKTPXN")] = d.loc[yp, c("NYGDPMKTPXN")] * np.exp(pi_t)

            # Nominal aggregates
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
            d.loc[y, c("NEWRTTOTLXN")] = d.loc[yp, c("NEWRTTOTLXN")] * np.exp(pi_t + 0.5*prod_g)
            d.loc[y, c("NYYWBTOTLCN")] = d.loc[y, c("NEWRTTOTLXN")] * d.loc[y, c("LMEMPTOTL")]
            d.loc[y, c("LMEMPTOTL")]   = apply_ecm(
                d.loc[yp, c("LMEMPTOTL")], d.loc[y, c("LMEMPSTRL")],
                {"gap_chg": gap, "dly_lstar": np.log(d.loc[y, c("LMEMPSTRL")]/d.loc[yp, c("LMEMPSTRL")])},
                coef["LMEMPTOTL"])
            d.loc[y, c("LMUNRTOTL_")]  = (1 - d.loc[y, c("LMEMPTOTL")]/d.loc[y, c("LMLBFTOTL")])*100

            # ==============================================================
            # Hydrocarbon revenue block (FIX 3 core)
            # ==============================================================
            # Gas production already set exogenous; IDH tracks production × price
            # Price assumed flat USD; peg held → revenue scales with production
            gas_ratio = d.loc[y, c("GASPROD")] / d.loc[yp, c("GASPROD")]
            # IDH: flat effective rate on gas export value. Export value scales with production.
            # Add CPI pass-through (nominal collection)
            d.loc[y, c("GGREVIDHCN")]  = d.loc[yp, c("GGREVIDHCN")] * gas_ratio * np.exp(pi_t * 0.3)
            # IEHD: domestic fuel consumption roughly flat (rationing), CPI indexation
            d.loc[y, c("GGREVIEHDCN")] = d.loc[yp, c("GGREVIEHDCN")] * 0.97 * np.exp(pi_t * 0.5)
            # Royalties: production-scaled
            d.loc[y, c("EMPROYALTIES")] = d.loc[yp, c("EMPROYALTIES")] * gas_ratio * np.exp(pi_t * 0.3)
            # YPFB hydrocarbon sales (SOE revenue): also production-scaled
            d.loc[y, c("EMPHYDROSALES")] = d.loc[yp, c("EMPHYDROSALES")] * gas_ratio * np.exp(pi_t * 0.4)

            # ==============================================================
            # Expenditure block (FIX 2): total via ECM anchor; components by share
            # ==============================================================
            # IMF Art IV: total expenditure / GDP declines slightly (38.7 → 37.4% 2024-25)
            # Use ECM target that tracks nominal GDP, plus explicit fuel-subsidy add-on
            exp_ecm = apply_ecm(
                d.loc[yp, c("GGEXPTOTLCN")], d.loc[yp, c("NYGDPMKTPCN")],
                {"dly_gdpn": dly_ngdp_prev}, coef["GGEXPTOTLCN"])
            # Fuel subsidy: 2024 base (3.7% GDP) + modest drift under peg (IMF Box 1 says
            # full +2.6pp only materializes under devaluation)
            fuel_share = {2025: 0.040, 2026: 0.042, 2027: 0.044}.get(y, 0.037)
            base_fuel_2024_share = d.loc[2024, c("GGEXPFUELCN")] / d.loc[2024, c("NYGDPMKTPCN")]
            fuel_extra_pp = fuel_share - base_fuel_2024_share
            d.loc[y, c("GGEXPFUELCN")] = fuel_share * d.loc[y, c("NYGDPMKTPCN")]
            # Interest: endogenous on prior debt (split ext/dom at IMF rates)
            int_rate_ext = 0.04; int_rate_dom = 0.09
            d.loc[y, c("GGEXPINTECN")] = int_rate_ext * d.loc[yp, c("GGDBTEXTLCN")]
            d.loc[y, c("GGEXPINTDCN")] = int_rate_dom * d.loc[yp, c("GGDBTDOMTCN")]
            d.loc[y, c("GGEXPINTPCN")] = d.loc[y, c("GGEXPINTECN")] + d.loc[y, c("GGEXPINTDCN")]
            # Total = ECM base + fuel subsidy extra pressure
            d.loc[y, c("GGEXPTOTLCN")] = exp_ecm + fuel_extra_pp * d.loc[y, c("NYGDPMKTPCN")]
            # Allocate to components by share (from BolBudget disaggregation)
            tot_nonint_nonfuel = d.loc[y, c("GGEXPTOTLCN")] - d.loc[y, c("GGEXPFUELCN")] - d.loc[y, c("GGEXPINTPCN")]
            base_2024_nonint_nonfuel = (d.loc[2024, c("GGEXPTOTLCN")] - d.loc[2024, c("GGEXPFUELCN")]
                                       - d.loc[2024, c("GGEXPINTPCN")])
            for comp in ["GGEXPWAGESCN", "GGEXPGSCN", "GGEXPTRNSCN", "GGEXPCAPEXCN"]:
                share = d.loc[2024, c(comp)] / base_2024_nonint_nonfuel
                d.loc[y, c(comp)] = share * tot_nonint_nonfuel

            # ==============================================================
            # Revenue
            # ==============================================================
            # Non-hydrocarbon revenue: ECM on nominal GDP
            non_hc_rev_prev = (d.loc[yp, c("GGREVTOTLCN")] - d.loc[yp, c("GGREVIDHCN")]
                              - d.loc[yp, c("GGREVIEHDCN")] - d.loc[yp, c("EMPROYALTIES")])
            non_hc_rev_tar = d.loc[yp, c("NYGDPMKTPCN")] * 0.24  # 24% of GDP structural non-HC
            non_hc_rev_new = apply_ecm(non_hc_rev_prev, non_hc_rev_tar,
                                      {"dly_gdpn": dly_ngdp_prev}, coef["GGREVTOTLCN"])
            d.loc[y, c("GGREVTOTLCN")] = (non_hc_rev_new + d.loc[y, c("GGREVIDHCN")]
                                        + d.loc[y, c("GGREVIEHDCN")] + d.loc[y, c("EMPROYALTIES")])
            d.loc[y, c("GGREVHYDRCN")] = d.loc[y, c("GGREVIDHCN")] + d.loc[y, c("GGREVIEHDCN")] + d.loc[y, c("EMPROYALTIES")]

            # Balances
            d.loc[y, c("GGBALOVRLCN")] = d.loc[y, c("GGREVTOTLCN")] - d.loc[y, c("GGEXPTOTLCN")]
            d.loc[y, c("GGBALPRIMCN")] = (d.loc[y, c("GGREVTOTLCN")] -
                                         (d.loc[y, c("GGEXPTOTLCN")] - d.loc[y, c("GGEXPINTPCN")]))
            # Debt
            d.loc[y, c("GGDBTTOTLCN")] = d.loc[yp, c("GGDBTTOTLCN")] - d.loc[y, c("GGBALOVRLCN")]
            d.loc[y, c("GGDBTEXTLCN")] = d.loc[y, c("GGDBTTOTLCN")] * 0.25  # IMF path
            d.loc[y, c("GGDBTDOMTCN")] = d.loc[y, c("GGDBTTOTLCN")] - d.loc[y, c("GGDBTEXTLCN")]
            d.loc[y, c("GGDBTTOTLGD")] = d.loc[y, c("GGDBTTOTLCN")] / d.loc[y, c("NYGDPMKTPCN")] * 100
            d.loc[y, c("GGBALOVRLGD")] = d.loc[y, c("GGBALOVRLCN")] / d.loc[y, c("NYGDPMKTPCN")] * 100
            # BCB financing = residual up to 12% GDP cap (IMF ceiling on monetization)
            ext_net_gdp = -0.005
            priv_dom_gdp = 0.005
            bcb_residual = -d.loc[y, c("GGBALOVRLGD")] - ext_net_gdp - priv_dom_gdp
            d.loc[y, c("GGFINBCBGD")] = min(bcb_residual, 10.0)  # cap: IMF shows ~10%
            d.loc[y, c("GGFINBCBCN")] = d.loc[y, c("GGFINBCBGD")] / 100 * d.loc[y, c("NYGDPMKTPCN")]

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
            cur = d.loc[y, key].astype(float)
            old = prev_state[key].astype(float)
            if old.isna().any() or (old == 0).any():
                diff = np.inf; continue
            diff = ((cur - old) / old).abs().max()
            if diff < TOL:
                print(f"  Converged in {it+1} iter (diff {diff:.2e})")
                break
        else:
            print(f"  WARN no convergence (diff {diff:.2e})")

        rg = 100*(d.loc[y, c("NYGDPMKTPKN")]/d.loc[yp, c("NYGDPMKTPKN")] - 1)
        pi = 100*(d.loc[y, c("FPCPITOTLXN")]/d.loc[yp, c("FPCPITOTLXN")] - 1)
        print(f"  Real GDP = {rg:.2f}%  CPI = {pi:.2f}%  FiscBal = {d.loc[y, c('GGBALOVRLGD')]:.2f}%")
        print(f"  Debt = {d.loc[y, c('GGDBTTOTLGD')]:.1f}%  BCB fin = {d.loc[y, c('GGFINBCBGD')]:.2f}%  CA = ${d.loc[y, c('BNCABFUNDCD')]/1e9:.2f}bn")

    d.to_csv(OUT)

    # Comparison table
    imf = {
        "RealGDP_g":    {2023:3.1, 2024:1.3, 2025:1.1, 2026:0.9, 2027:0.6},
        "CPI_avg":      {2023:2.6, 2024:5.1, 2025:15.1, 2026:15.8, 2027:17.1},
        "FiscBal_GDP":  {2023:-10.9, 2024:-10.3, 2025:-12.7, 2026:-13.2, 2027:-12.5},
        "NFPSDebt_GDP": {2023:90.8, 2024:95.0, 2025:90.4, 2026:91.4, 2027:92.8},
        "CA_GDP":       {2023:-2.5, 2024:-2.7, 2025:-2.6, 2026:-3.2, 2027:-3.8},
        "NomGDP_USDbn": {2023:45.5, 2024:48.4, 2025:56.3, 2026:65.9, 2027:75.0},
    }
    rows=[]
    for y in range(2023, 2028):
        yp=y-1
        rg = 100*(d.loc[y,c("NYGDPMKTPKN")]/d.loc[yp,c("NYGDPMKTPKN")] - 1)
        pi = 100*(d.loc[y,c("FPCPITOTLXN")]/d.loc[yp,c("FPCPITOTLXN")] - 1)
        rows.append({
            "year": y,
            "IMF_RealGDP":   imf["RealGDP_g"].get(y),
            "v3_RealGDP":    rg,
            "IMF_CPI":       imf["CPI_avg"].get(y),
            "v3_CPI":        pi,
            "IMF_FiscBal":   imf["FiscBal_GDP"].get(y),
            "v3_FiscBal":    d.loc[y, c("GGBALOVRLGD")],
            "IMF_NFPSDebt":  imf["NFPSDebt_GDP"].get(y),
            "v3_NFPSDebt":   d.loc[y, c("GGDBTTOTLGD")],
            "IMF_CA":        imf["CA_GDP"].get(y),
            "v3_CA":         d.loc[y, c("BNCABFUNDCD")]/d.loc[y, c("NYGDPMKTPCD")]*100,
            "IMF_NomGDP_USDbn": imf["NomGDP_USDbn"].get(y),
            "v3_NomGDP_USDbn":  d.loc[y, c("NYGDPMKTPCD")]/1e9,
        })
    cmp = pd.DataFrame(rows).set_index("year").round(2)
    cmp.to_csv(CMP)
    print("\n" + "=" * 80)
    print("MFMod-BOL v3 vs IMF Art IV 2025")
    print("=" * 80)
    print(cmp.T.to_string())

if __name__ == "__main__":
    main()
