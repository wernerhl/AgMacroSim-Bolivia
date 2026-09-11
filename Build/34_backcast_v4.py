"""
MFMod-BOL v4 — Out-of-sample backcast.
Estimates ECMs on 1995-2019 sample, then simulates 2020-2024.
Reports forecast errors vs actual to validate model dynamics.
"""
import os, json
import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = "/Users/whl/Documents/whl.BolBudget/MFMOD_BOL"
DATA = os.path.join(ROOT, "Rawdata", "bol_data_v3.csv")
OUT  = os.path.join(ROOT, "Output", "BACKCAST_v4.csv")

CTY = "BOL"
def c(x): return f"{CTY}{x}"

def dlog(s): return np.log(s).diff()

def ecm(dep, lr, sr=None, sample=(1995, 2019), clip_alpha_zero=False):
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
    return {
        "alpha": alpha, "theta": theta,
        "betas": {k: float(res.params.get(k, 0.0)) for k in (sr or {})},
        "rsq": float(res.rsquared), "nobs": int(res.nobs),
    }

def main():
    d = pd.read_csv(DATA, index_col="year"); d.index = d.index.astype(int)
    # Re-estimate on 1995-2019
    sample = (1995, 2019)
    coef = {}
    labinc = 0.55 * d[c("NYGDPFCSTCN")] / d[c("NECONPRVTXN")]
    coef["NECONPRVTKN"] = ecm(d[c("NECONPRVTKN")], labinc,
                              {"dly_inc": labinc, "dly_gdp": d[c("NYGDPMKTPKN")]}, sample)
    coef["NEGDIFPRVKN"] = ecm(d[c("NEGDIFPRVKN")], d[c("NYGDPPOTLKN")],
                              {"dly_gdp": d[c("NYGDPMKTPKN")], "dly_rate": d[c("FMLBLPOLYFR")]},
                              sample, clip_alpha_zero=True)
    coef["NEEXPGNFSKN"] = ecm(d[c("NEEXPGNFSKN")], d[c("NYGDPMKTPCD")] * 1.5,
                              {"dly_xmkt": d[c("NYGDPMKTPCD")]}, sample)
    gde = d[c("NECONPRVTKN")] + d[c("NECONGOVTKN")] + d[c("NEGDIFTOTKN")] + d[c("NEEXPGNFSKN")]
    coef["NEIMPGNFSKN"] = ecm(d[c("NEIMPGNFSKN")], gde, {"dly_gde": gde}, sample)

    # Generate predictions for 2020-2024 using ECMs (open-loop)
    # Keep exog as historical actuals
    preds = {"NYGDPMKTPKN": [], "NECONPRVTKN": [], "NEEXPGNFSKN": [], "NEIMPGNFSKN": []}
    years = [2020, 2021, 2022, 2023, 2024]
    for var, cf in [("NECONPRVTKN", coef["NECONPRVTKN"]),
                    ("NEGDIFPRVKN", coef["NEGDIFPRVKN"]),
                    ("NEEXPGNFSKN", coef["NEEXPGNFSKN"]),
                    ("NEIMPGNFSKN", coef["NEIMPGNFSKN"])]:
        for y in years:
            # Simulate this variable using lag + ECM
            # For backcast we use ACTUAL lagged data and predict Δ
            yp = y - 1
            lag_val = d.loc[yp, c(var)]
            # Determine LR and SR by variable
            if var == "NECONPRVTKN":
                lr = 0.55 * d.loc[yp, c("NYGDPFCSTCN")] / d.loc[yp, c("NECONPRVTXN")]
                sr = {"dly_inc": np.log((0.55*d.loc[y, c("NYGDPFCSTCN")]/d.loc[y, c("NECONPRVTXN")]) /
                                        (0.55*d.loc[yp, c("NYGDPFCSTCN")]/d.loc[yp, c("NECONPRVTXN")])),
                      "dly_gdp": np.log(d.loc[y, c("NYGDPMKTPKN")]/d.loc[yp, c("NYGDPMKTPKN")])}
            elif var == "NEGDIFPRVKN":
                lr = d.loc[yp, c("NYGDPPOTLKN")]
                sr = {"dly_gdp": np.log(d.loc[y, c("NYGDPMKTPKN")]/d.loc[yp, c("NYGDPMKTPKN")]),
                      "dly_rate": d.loc[y, c("FMLBLPOLYFR")] - d.loc[yp, c("FMLBLPOLYFR")]}
            elif var == "NEEXPGNFSKN":
                lr = d.loc[yp, c("NYGDPMKTPCD")] * 1.5
                sr = {"dly_xmkt": np.log(d.loc[y, c("NYGDPMKTPCD")]/d.loc[yp, c("NYGDPMKTPCD")])}
            elif var == "NEIMPGNFSKN":
                lr_c = (d.loc[yp, c("NECONPRVTKN")] + d.loc[yp, c("NECONGOVTKN")]
                        + d.loc[yp, c("NEGDIFTOTKN")] + d.loc[yp, c("NEEXPGNFSKN")])
                lr = lr_c
                sr = {"dly_gde": np.log(((d.loc[y, c("NECONPRVTKN")] + d.loc[y, c("NECONGOVTKN")]
                                          + d.loc[y, c("NEGDIFTOTKN")] + d.loc[y, c("NEEXPGNFSKN")])) / lr_c)}
            ec = np.log(lag_val) - np.log(lr)
            dly = cf["alpha"] - cf["theta"] * ec
            for k, b in cf["betas"].items():
                if k in sr: dly += b * sr[k]
            pred = lag_val * np.exp(np.clip(dly, -0.25, 0.25))
            actual = d.loc[y, c(var)]
            preds.setdefault(var, []).append({"year": y, "pred": pred, "actual": actual,
                                             "pct_err": 100*(pred/actual - 1)})

    rows = []
    for var, lst in preds.items():
        if not isinstance(lst, list): continue
        for r in lst:
            rows.append({"var": var, **r})
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)

    print("=" * 70)
    print("BACKCAST 2020-2024 (estimated 1995-2019)  —  % error vs actual")
    print("=" * 70)
    pivot = out.pivot(index="year", columns="var", values="pct_err").round(1)
    print(pivot.to_string())
    print("\nRMSE by variable:")
    for v in pivot.columns:
        rmse = np.sqrt(np.mean(pivot[v] ** 2))
        print(f"  {v:<18s}: {rmse:.2f}%")
    print(f"\nSaved: {OUT}")

if __name__ == "__main__":
    main()
