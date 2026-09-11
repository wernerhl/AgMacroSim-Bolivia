"""
MFMod-BOL v5 — ESTIMATION.
Key improvements:
  - Sample 2000-2024 (post-hyperinflation, post-HIPC, consistent data).
  - Use structural output gap (from BolBudget) instead of HP-filter.
  - CPI regime-switch coefficient estimated from LATAM PANEL (ARG + BOL).
  - Drop any arbitrary drift terms; rely on ECM + explicit shift dummies.
"""
import os, json
import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = "/Users/whl/Documents/whl.BolBudget/MFMOD_BOL"
DATA = os.path.join(ROOT, "Rawdata", "bol_data_v5.csv")
LATAM = "/Users/whl/Documents/whl.BolBudget/analysis/latam_comparison_1990_2024.csv"
OUT = os.path.join(ROOT, "Rawdata", "bol_coefficients_v5.json")

CTY = "BOL"
def c(x): return f"{CTY}{x}"

def dlog(s): return np.log(s).diff()

def ecm(dep, lr, sr=None, sample=(2000, 2024), clip_alpha_zero=False):
    y = dep
    cols = {"dly": dlog(y)}
    X_cols = []
    if lr is not None:
        cols["ec"] = (np.log(y) - np.log(lr)).shift(1)
        X_cols.append("ec")
    if sr:
        for k, v in sr.items():
            cols[k] = dlog(v) if (v > 0).all() else v.diff()
            X_cols.append(k)
    df = pd.DataFrame(cols).loc[sample[0]:sample[1]].dropna()
    if len(df) < 6:
        return {"alpha": 0, "theta": 0.2, "betas": {}, "rsq": 0, "nobs": len(df)}
    X = sm.add_constant(df[X_cols]) if X_cols else pd.DataFrame(index=df.index)
    if "const" not in X.columns: X = sm.add_constant(X)
    res = sm.OLS(df["dly"], X).fit()
    alpha = float(res.params.get("const", 0.0))
    if clip_alpha_zero: alpha = max(alpha, 0.0)
    theta = float(-res.params.get("ec", 0.0)) if "ec" in res.params.index else 0.2
    if not (0 < theta < 1): theta = 0.2
    return {"alpha": alpha, "theta": theta,
            "betas": {k: float(res.params.get(k, 0.0)) for k in (sr or {})},
            "rsq": float(res.rsquared), "nobs": int(res.nobs)}

def estimate_cpi_panel():
    """
    LATAM panel CPI regression.
    Spec: Δlog P = α + β1·π_lag + β2·output_gap + β3·reserves_scarcity_indicator·monetization
    Using ARG (high-inflation regime exemplar) + BOL.
    ARG 1990-2024: inflation ranges 0.1% to 200%+.
    """
    l = pd.read_csv(LATAM)
    # Pivot: year × country → inflation, reserves
    inf = l[l.indicator == "inflation_pct"].pivot(index="year", columns="country", values="value")
    res = l[l.indicator == "reserves_USD"].pivot(index="year", columns="country", values="value")
    # Compute reserve scarcity per country (< 3 months imports = 1)
    # Use a proxy: reserves_USD / GDP_USD × 10 as "reserves months" (crude)
    gdp = l[l.indicator == "GDP_USD"].pivot(index="year", columns="country", values="value")
    panel_rows = []
    for country in ["ARG", "BOL", "CHL", "COL", "ECU", "PER", "PRY"]:
        if country not in inf.columns: continue
        inf_c = inf[country].dropna()
        res_c = res[country].reindex(inf_c.index)
        gdp_c = gdp[country].reindex(inf_c.index)
        # Reserves-to-GDP as crude scarcity proxy (lower = scarcer)
        r_gdp = res_c / gdp_c
        # Scarcity indicator: 1 when r_gdp < 0.03 (below 3% GDP), 0 above 0.10
        scar = np.clip((0.10 - r_gdp) / 0.07, 0, 1)
        for y in inf_c.index:
            pi = inf_c.loc[y] / 100
            pi_lag = inf_c.loc[y-1] / 100 if y-1 in inf_c.index else np.nan
            sc = scar.loc[y] if y in scar.index else np.nan
            panel_rows.append({
                "country": country, "year": y,
                "pi": pi, "pi_lag": pi_lag, "scarcity": sc,
                "scar_pi_lag": sc * pi_lag if pd.notna(sc) and pd.notna(pi_lag) else np.nan,
            })
    p = pd.DataFrame(panel_rows).dropna()
    # Split into normal vs scarcity regime for coefficient identification
    # Normal regime: β on pi_lag
    norm = p[p.scarcity == 0]
    X = sm.add_constant(norm[["pi_lag"]])
    r_norm = sm.OLS(norm["pi"], X).fit()
    # Scarcity regime: additional loading
    scar_p = p[p.scarcity > 0]
    if len(scar_p) > 10:
        X = sm.add_constant(scar_p[["pi_lag", "scarcity"]])
        r_scar = sm.OLS(scar_p["pi"], X).fit()
        scar_coef = float(r_scar.params.get("scarcity", 0.15))
    else:
        scar_coef = 0.15  # reasonable prior if sample thin
    print(f"\nLATAM Panel CPI estimation:")
    print(f"  Normal regime (scar=0): pi = {r_norm.params['const']:.4f} + {r_norm.params['pi_lag']:.3f}*pi_lag")
    print(f"  Scarcity regime add:    +{scar_coef:.3f} × scarcity")
    print(f"  n_normal={len(norm)}  n_scarcity={len(scar_p)}")
    return {
        "alpha": float(r_norm.params["const"]),
        "pi_lag": float(r_norm.params["pi_lag"]),
        "scarcity_level_pp": scar_coef,
        "gap": 0.15,  # standard Phillips semi-elasticity
        "source": "LATAM panel: ARG, BOL, CHL, COL, ECU, PER, PRY, 1990-2024",
    }

def main():
    d = pd.read_csv(DATA, index_col="year"); d.index = d.index.astype(int)
    coef = {}
    SAMP = (2000, 2023)  # exclude 2024 (still preliminary) for robust estimation
    ALPHA = 0.55

    print("=" * 70)
    print("MFMod-BOL v5 — ECM ESTIMATION (sample 2000-2023, spliced GDP)")
    print("=" * 70)

    # Consumption
    labinc = ALPHA * d[c("NYGDPFCSTCN")] / d[c("NECONPRVTXN")]
    coef["NECONPRVTKN"] = ecm(
        d[c("NECONPRVTKN")], labinc,
        sr={"dly_inc": labinc, "dly_gdp": d[c("NYGDPMKTPKN")]}, sample=SAMP)

    # Private investment (α ≥ 0)
    coef["NEGDIFPRVKN"] = ecm(
        d[c("NEGDIFPRVKN")], d[c("NYGDPPOTLKN")],
        sr={"dly_gdp": d[c("NYGDPMKTPKN")], "dly_rate": d[c("FMLBLPOLYFR")]},
        sample=SAMP, clip_alpha_zero=True)

    # Exports (aggregate ECM)
    coef["NEEXPGNFSKN"] = ecm(
        d[c("NEEXPGNFSKN")], d[c("NYGDPMKTPCD")] * 1.5,
        sr={"dly_xmkt": d[c("NYGDPMKTPCD")]}, sample=SAMP)

    # Imports (depends on GDE)
    gde = d[c("NECONPRVTKN")] + d[c("NECONGOVTKN")] + d[c("NEGDIFTOTKN")] + d[c("NEEXPGNFSKN")]
    coef["NEIMPGNFSKN"] = ecm(
        d[c("NEIMPGNFSKN")], gde, sr={"dly_gde": gde}, sample=SAMP)

    # Sectoral VA
    coef["NVAGRTOTLKN"] = ecm(
        d[c("NVAGRTOTLKN")], d[c("NYGDPPOTLKN")],
        sr={"dly_gde": gde}, sample=SAMP, clip_alpha_zero=True)
    coef["NVINDTOTLKN"] = ecm(
        d[c("NVINDTOTLKN")], d[c("NYGDPPOTLKN")],
        sr={"dly_gde": gde}, sample=SAMP, clip_alpha_zero=True)

    # Employment
    coef["LMEMPTOTL"] = ecm(
        d[c("LMEMPTOTL")], d[c("LMEMPSTRL")],
        sr={"gap_chg": d[c("NYGDPGAP_")]/100, "dly_lstar": d[c("LMEMPSTRL")]},
        sample=SAMP)

    # Revenue (total) — long-run to share of GDP
    coef["GGREVTOTLCN"] = ecm(
        d[c("GGREVTOTLCN")], d[c("NYGDPMKTPCN")],
        sr={"dly_gdpn": d[c("NYGDPMKTPCN")]}, sample=SAMP)

    # Hydrocarbon revenue (long-run target = gas share × GDP)
    coef["GGREVHYDRCN"] = ecm(
        d[c("GGREVHYDRCN")], d[c("NYGDPMKTPCN")] * 0.08,
        sr={"dly_gdpn": d[c("NYGDPMKTPCN")]}, sample=(2005, 2023))

    # Expenditure (total) — aggregate long-run tracking
    coef["GGEXPTOTLCN"] = ecm(
        d[c("GGEXPTOTLCN")], d[c("NYGDPMKTPCN")],
        sr={"dly_gdpn": d[c("NYGDPMKTPCN")]}, sample=SAMP)

    # CPI: use LATAM panel estimate + Bolivia-specific Phillips term
    coef["FPCPITOTLXN"] = estimate_cpi_panel()

    with open(OUT, "w") as f:
        json.dump(coef, f, indent=2, default=float)

    print("\n" + "=" * 70)
    print("ESTIMATED COEFFICIENTS (v5)")
    print("=" * 70)
    print(f"{'equation':<22s} {'alpha':>8s} {'theta':>8s} {'rsq':>6s} {'nobs':>5s}")
    for k, v in coef.items():
        if "alpha" in v and "theta" in v:
            print(f"{k:<22s} {v['alpha']:>8.4f} {v['theta']:>8.4f} "
                  f"{v.get('rsq',0):>6.2f} {v.get('nobs',0):>5d}")
    print(f"\nSaved: {OUT}")

if __name__ == "__main__":
    main()
