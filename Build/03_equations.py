"""
Step 3: Estimate behavioral equations of MFMod-BOL using 1995-2024 data.
All equations follow WPS8965 (Burns et al. 2019) ECM form:
    Delta(y_t) = alpha - theta*[y_{t-1} - X_{t-1}] + beta*Delta(y_{t-1}) + gamma*Delta(z_t)

For each equation: estimate theta, short-run betas via OLS on the first-differenced form.
Where identification fails (e.g. commodity-exporter peculiarities), we impose paper priors.
Output: Rawdata/bol_coefficients.json (coefficient dict for step 4).
"""
import os
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "Rawdata", "bol_data.csv")
OUT  = os.path.join(ROOT, "Rawdata", "bol_coefficients.json")

CTY = "BOL"
def c(x): return f"{CTY}{x}"

# Estimation sample: post-stabilization, pre-boom-bust mix
SAMP_START, SAMP_END = 1995, 2024

def log(x): return np.log(x)
def dlog(s): return np.log(s).diff()

def ecm_estimate(dep_level: pd.Series,
                 lr_rhs: pd.Series | None,
                 sr_vars: dict[str, pd.Series] | None = None,
                 sample=(SAMP_START, SAMP_END)) -> dict:
    """
    Estimate Delta log(y_t) = alpha - theta*[log(y_{t-1}) - log(lr_rhs_{t-1})]
                              + sum_i beta_i * Delta log(sr_var_i_t)
    Returns dict with alpha, theta, and short-run betas.
    """
    y = dep_level.copy()
    dly = dlog(y)
    cols = {"dly": dly}
    X_cols = []
    if lr_rhs is not None:
        # ECM term evaluated at t-1
        ec = (np.log(y) - np.log(lr_rhs)).shift(1)
        cols["ec"] = ec
        X_cols.append("ec")
    if sr_vars:
        for k, v in sr_vars.items():
            cols[k] = dlog(v) if (v > 0).all() else v.diff()
            X_cols.append(k)
    df = pd.DataFrame(cols).loc[sample[0]:sample[1]].dropna()
    if len(df) < 6:
        return {"alpha": 0, "theta": 0.2, "betas": {}, "nobs": len(df), "note": "insufficient"}
    X = sm.add_constant(df[X_cols]) if X_cols else pd.DataFrame(index=df.index)
    X = sm.add_constant(X) if "const" not in X.columns else X
    try:
        res = sm.OLS(df["dly"], X).fit()
        alpha = float(res.params.get("const", 0.0))
        theta = float(-res.params.get("ec", 0.0)) if "ec" in res.params.index else 0.0
        betas = {k: float(res.params.get(k, 0.0)) for k in (sr_vars or {})}
        return {
            "alpha": alpha,
            "theta": theta if 0 < theta < 1 else 0.2,
            "betas": betas,
            "rsq": float(res.rsquared),
            "nobs": int(res.nobs),
        }
    except Exception as e:
        return {"alpha": 0, "theta": 0.2, "betas": {}, "note": f"fail: {e}"}

def main():
    d = pd.read_csv(DATA, index_col="year")
    d.index = d.index.astype(int)
    coef = {}

    print("=" * 60)
    print("ESTIMATING BOL MFMod BEHAVIORAL EQUATIONS  (1995-2024)")
    print("=" * 60)

    # ---- (1) Private consumption ECM -------------------------------------
    # Eq 4 paper (simplified): Dc = a - theta*[c_{t-1} - log((YD+TR)/Pc)_{t-1}]
    #                               + beta*D(YD+TR)/Pc + theta*D(wealth/Pc)
    # Proxies: real disposable income ~ real private consumption base
    # Use labor income + remittances
    labinc = d[c("NYYWBTOTLCN")] / d[c("NECONPRVTXN")]        # real labor inc
    remit  = d[c("BXFSTREMTCD")] * d[c("PANUSATLS")] / d[c("NECONPRVTXN")]  # real remit
    inc_real = (labinc + remit.fillna(0))
    r = ecm_estimate(
        d[c("NECONPRVTKN")],
        lr_rhs=inc_real,
        sr_vars={"dly_inc": inc_real, "dly_gdp": d[c("NYGDPMKTPKN")]},
    )
    coef["NECONPRVTKN"] = r
    print(f"\nPrivate consumption (NECONPRVTKN): theta={r['theta']:.3f} R2={r.get('rsq',0):.2f}  n={r['nobs']}")

    # ---- (2) Private investment ECM --------------------------------------
    # Long-run: Ip* = (delta+g)(1-alpha)P*Y*/R (paper eq 8)
    # Simplified: Ip* proportional to potential GDP
    r = ecm_estimate(
        d[c("NEGDIFPRVKN")],
        lr_rhs=d[c("NYGDPPOTLKN")],
        sr_vars={"dly_gdp": d[c("NYGDPMKTPKN")], "dly_rate": d[c("FMLBLPOLYFR")]},
    )
    coef["NEGDIFPRVKN"] = r
    print(f"Private investment (NEGDIFPRVKN): theta={r['theta']:.3f} R2={r.get('rsq',0):.2f}  n={r['nobs']}")

    # ---- (3) Real exports ECM --------------------------------------------
    # Long-run: x_t ~ xmkt_t + rel_price (paper eq 12)
    # For BOL, export volume is commodity-driven. Use gas+minerals export value deflated
    # Proxy external demand (XMKT) = US GDP real path (BOL neighbor effect)
    # Here we approximate with world GDP proxy via WDI later; for now use total trade value/CPI
    # Short-run: GDP growth of partners (approx via nom exports USD / US CPI)
    x_val_usd = d[c("BXGSRMRCHCD")]
    # Use Bolivia nominal GDP USD as partner-demand proxy (crude)
    xmkt_proxy = d[c("NYGDPMKTPCD")] * 1.5  # scale to rough world demand level
    r = ecm_estimate(
        d[c("NEEXPGNFSKN")],
        lr_rhs=xmkt_proxy,
        sr_vars={"dly_xmkt": xmkt_proxy},
    )
    coef["NEEXPGNFSKN"] = r
    print(f"Real exports (NEEXPGNFSKN): theta={r['theta']:.3f} R2={r.get('rsq',0):.2f}  n={r['nobs']}")

    # ---- (4) Real imports ECM --------------------------------------------
    # Long-run: m_t ~ domestic demand + relative import price
    gde = (d[c("NECONPRVTKN")] + d[c("NECONGOVTKN")]
           + d[c("NEGDIFTOTKN")] + d[c("NEEXPGNFSKN")])
    r = ecm_estimate(
        d[c("NEIMPGNFSKN")],
        lr_rhs=gde,
        sr_vars={"dly_gde": gde},
    )
    coef["NEIMPGNFSKN"] = r
    print(f"Real imports (NEIMPGNFSKN): theta={r['theta']:.3f} R2={r.get('rsq',0):.2f}  n={r['nobs']}")

    # ---- (5) Agriculture VA ----------------------------------------------
    r = ecm_estimate(
        d[c("NVAGRTOTLKN")],
        lr_rhs=d[c("NYGDPPOTLKN")],
        sr_vars={"dly_gde": gde + d[c("NEEXPGNFSKN")]},
    )
    coef["NVAGRTOTLKN"] = r
    print(f"Agriculture VA (NVAGRTOTLKN): theta={r['theta']:.3f} R2={r.get('rsq',0):.2f}  n={r['nobs']}")

    # ---- (6) Industry VA -------------------------------------------------
    r = ecm_estimate(
        d[c("NVINDTOTLKN")],
        lr_rhs=d[c("NYGDPPOTLKN")],
        sr_vars={"dly_gde": gde + d[c("NEEXPGNFSKN")]},
    )
    coef["NVINDTOTLKN"] = r
    print(f"Industry VA (NVINDTOTLKN): theta={r['theta']:.3f} R2={r.get('rsq',0):.2f}  n={r['nobs']}")

    # ---- (7) CPI (Phillips-curve-like ECM on consumption deflator) -------
    # Simplify to: D log P_c = alpha + beta1*gap + beta2*D log P_{c,-1} + beta3*D log ULC
    # Unit labor cost proxy: wage / labor productivity
    ulc = d[c("NEWRTTOTLXN")] / (d[c("NYGDPMKTPKN")] / d[c("LMEMPTOTL")])
    r = ecm_estimate(
        d[c("FPCPITOTLXN")],
        lr_rhs=ulc * d[c("FPCPITOTLXN")].iloc[0] / ulc.iloc[0],  # anchor LR
        sr_vars={"gap": d[c("NYGDPGAP_")] / 100, "dly_ulc": ulc},
    )
    coef["FPCPITOTLXN"] = r
    print(f"CPI (FPCPITOTLXN): theta={r['theta']:.3f} R2={r.get('rsq',0):.2f}  n={r['nobs']}")

    # ---- (8) GDP deflator at factor cost --------------------------------
    # Track CPI: d log P_fcst = alpha + beta * d log CPI
    r = ecm_estimate(
        d[c("NYGDPFCSTXN")],
        lr_rhs=d[c("FPCPITOTLXN")] * (d[c("NYGDPFCSTXN")].iloc[0] / d[c("FPCPITOTLXN")].iloc[0]),
        sr_vars={"dly_cpi": d[c("FPCPITOTLXN")]},
    )
    coef["NYGDPFCSTXN"] = r
    print(f"GDP fc deflator (NYGDPFCSTXN): theta={r['theta']:.3f} R2={r.get('rsq',0):.2f}  n={r['nobs']}")

    # ---- (9) Import deflator --------------------------------------------
    # Long-run: P_m ~ world price (Keyfitz proxy = CPI) * FX  (BOL peg so FX flat)
    world_p = d[c("FPCPITOTLXN")] * d[c("PANUSATLS")]
    r = ecm_estimate(
        d[c("NEIMPGNFSXN")],
        lr_rhs=world_p * (d[c("NEIMPGNFSXN")].iloc[0] / world_p.iloc[0]),
        sr_vars={"dly_wp": world_p, "dly_cpi": d[c("FPCPITOTLXN")]},
    )
    coef["NEIMPGNFSXN"] = r
    print(f"Import deflator (NEIMPGNFSXN): theta={r['theta']:.3f} R2={r.get('rsq',0):.2f}  n={r['nobs']}")

    # ---- (10) Export deflator -------------------------------------------
    r = ecm_estimate(
        d[c("NEEXPGNFSXN")],
        lr_rhs=world_p * (d[c("NEEXPGNFSXN")].iloc[0] / world_p.iloc[0]),
        sr_vars={"dly_wp": world_p, "dly_cpi": d[c("FPCPITOTLXN")]},
    )
    coef["NEEXPGNFSXN"] = r
    print(f"Export deflator (NEEXPGNFSXN): theta={r['theta']:.3f} R2={r.get('rsq',0):.2f}  n={r['nobs']}")

    # ---- (11) Nominal wage ECM  (paper eq 23) ----------------------------
    # D w_t = a + theta*[w - mpl - P_c]_{t-1} + gamma*D w_{t-1}
    #         + (1-gamma)*(D P_c + D y* - D L*) + beta*(UNR - UNR*)
    # LR target: nominal wage = MPL × CPI  (MPL = alpha * Y*/L*)
    mpl = ALPHA = 0.55
    Ystar = d[c("NYGDPPOTLKN")]
    Lstar = d[c("LMEMPSTRL")]
    nom_mpl = mpl * (Ystar / Lstar) * d[c("FPCPITOTLXN")] / d[c("FPCPITOTLXN")].iloc[0] * d[c("NEWRTTOTLXN")].iloc[0]
    r = ecm_estimate(
        d[c("NEWRTTOTLXN")],
        lr_rhs=nom_mpl,
        sr_vars={"dly_cpi": d[c("FPCPITOTLXN")], "gap": d[c("NYGDPGAP_")] / 100},
    )
    coef["NEWRTTOTLXN"] = r
    print(f"Nominal wage (NEWRTTOTLXN): theta={r['theta']:.3f} R2={r.get('rsq',0):.2f}  n={r['nobs']}")

    # ---- (12) Employment ECM (paper eq 22) -------------------------------
    # D l_t = beta1*[l-l*]_{t-1} + beta2*D YGAP + beta3*(D real wage - D labor prod) + D l*
    r = ecm_estimate(
        d[c("LMEMPTOTL")],
        lr_rhs=d[c("LMEMPSTRL")],
        sr_vars={"gap_chg": d[c("NYGDPGAP_")] / 100, "dly_lstar": d[c("LMEMPSTRL")]},
    )
    coef["LMEMPTOTL"] = r
    print(f"Employment (LMEMPTOTL): theta={r['theta']:.3f} R2={r.get('rsq',0):.2f}  n={r['nobs']}")

    # ---- (13) Fiscal: government nominal spending (paper eq 25) ----------
    # D log G = beta1 + beta2*[g - y^N]_{t-1} + beta3*D log G_{t-1} + (1-beta3)*D log Y^N
    r = ecm_estimate(
        d[c("GGEXPTOTLCN")],
        lr_rhs=d[c("NYGDPMKTPCN")],
        sr_vars={"dly_gdpn": d[c("NYGDPMKTPCN")]},
        sample=(2010, 2024),
    )
    coef["GGEXPTOTLCN"] = r
    print(f"Total govt expenditure (GGEXPTOTLCN): theta={r['theta']:.3f} R2={r.get('rsq',0):.2f}  n={r['nobs']}")

    # ---- (14) Fiscal: government revenue (pinned to nominal GDP) ---------
    r = ecm_estimate(
        d[c("GGREVTOTLCN")],
        lr_rhs=d[c("NYGDPMKTPCN")],
        sr_vars={"dly_gdpn": d[c("NYGDPMKTPCN")]},
        sample=(2010, 2024),
    )
    coef["GGREVTOTLCN"] = r
    print(f"Total govt revenue (GGREVTOTLCN): theta={r['theta']:.3f} R2={r.get('rsq',0):.2f}  n={r['nobs']}")

    # Save coefficients
    with open(OUT, "w") as f:
        json.dump(coef, f, indent=2, default=float)
    print(f"\nSaved {OUT}")

    # Summary table
    print("\n" + "=" * 60)
    print("SUMMARY OF ESTIMATED COEFFICIENTS")
    print("=" * 60)
    print(f"{'equation':<20s} {'alpha':>8s} {'theta':>8s} {'rsq':>6s} {'nobs':>5s}")
    for k, v in coef.items():
        print(f"{k:<20s} {v['alpha']:>8.4f} {v['theta']:>8.4f} {v.get('rsq',0):>6.2f} {v['nobs']:>5d}")

if __name__ == "__main__":
    main()
