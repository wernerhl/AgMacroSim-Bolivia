"""
MFMod-BOL v2 — Extend exogenous 2025-2027.
Calibrated to IMF Art IV 2025 (CR 25/116) assumptions:
  - Peg held at 6.91 Bs/USD
  - Lending rate flat at 2024 value
  - Population +1.1%
  - World demand proxy +5% USD
  - TFP: extend at historical CAGR 2014-2024
  - Reserves: decline per IMF path (2025: 2.1bn; 2026: 2.2bn; 2027: 2.1bn)
  - Reserve-scarcity: stays at 1.0 (critical regime)
  - Fuel-subsidy pressure: rising with parallel-FX gap
  - Hydrocarbon production decline: -15% volume/yr on gas sub-component
"""
import os
import numpy as np
import pandas as pd

ROOT = "/Users/whl/Documents/whl.BolBudget/MFMOD_BOL"
DATA = os.path.join(ROOT, "Rawdata", "bol_data_v2.csv")
OUT  = os.path.join(ROOT, "Rawdata", "bol_data_extended_v2.csv")

CTY = "BOL"
def c(x): return f"{CTY}{x}"

FORECAST = [2025, 2026, 2027]
LAST_HIST = 2024

def main():
    d = pd.read_csv(DATA, index_col="year")
    d.index = d.index.astype(int)

    # Add forecast rows
    for y in FORECAST:
        if y not in d.index:
            d.loc[y] = pd.NA
    d = d.sort_index()

    # TFP growth
    tfp = d[c("NYGDPTFP")].dropna()
    if 2014 in tfp.index and 2024 in tfp.index:
        g_tfp = (tfp.loc[2024] / tfp.loc[2014]) ** (1/10) - 1
    else:
        g_tfp = -0.010
    print(f"TFP growth 2014-24: {g_tfp*100:.2f}%")

    # Exogenous growth rates
    EXG = {
        c("PANUSATLS"):    0.00,
        c("FMLBLPOLYFR"):  0.00,
        c("SPPOPTOTL"):    0.011,
        c("SPPOP1564TO"):  0.013,
        c("SPPOPWORK"):    0.013,
        c("LMPRTSTRL_"):   0.00,
        c("LMUNRSTRL_"):   0.00,
        c("NYGDPTFP"):     g_tfp,
        c("NEGDISTKBKN"):  0.00,
        c("NEGDISTKBCN"):  0.12,  # nominal grows with CPI
        c("NYGDPDISCKN"):  0.00,
    }

    for col, g in EXG.items():
        if col not in d.columns or pd.isna(d.loc[LAST_HIST, col]):
            continue
        last = d.loc[LAST_HIST, col]
        for i, y in enumerate(FORECAST, start=1):
            d.loc[y, col] = last * (1 + g) ** i

    # Structural employment
    for y in FORECAST:
        wap    = d.loc[y, c("SPPOP1564TO")]
        lfpr_s = d.loc[y, c("LMPRTSTRL_")]
        unr_s  = d.loc[y, c("LMUNRSTRL_")]
        d.loc[y, c("LMEMPSTRL")] = wap * lfpr_s/100 * (1 - unr_s/100)
        d.loc[y, c("LMPRTTOTL_")] = d.loc[LAST_HIST, c("LMPRTTOTL_")]
        d.loc[y, c("LMLBFTOTL")] = wap * d.loc[y, c("LMPRTTOTL_")] / 100

    # World demand USD (already populated for hist; extend)
    last_xmkt = d.loc[LAST_HIST, c("NYGDPMKTPCD")] * 1.5
    for y in d.index[d.index <= LAST_HIST]:
        d.loc[y, c("XMKT_USD")] = d.loc[y, c("NYGDPMKTPCD")] * 1.5
    for i, y in enumerate(FORECAST, start=1):
        d.loc[y, c("XMKT_USD")] = last_xmkt * (1.05) ** i

    # ---- Reserves path (IMF Art IV Text Table 3) ---------------------
    res_fcst = {2025: 2118, 2026: 2199, 2027: 2160}  # USD millions
    for y, r in res_fcst.items():
        d.loc[y, c("FIRESGRSCD")] = r
    # Recompute months of imports with forecast reserves (requires imports 2025-27 but we'll compute
    # the scarcity indicator dynamically in solver). Prepare initial from 2024 level.
    # Reserve scarcity stays at 1.0 through forecast (reserves critically low)
    for y in FORECAST:
        d.loc[y, c("RES_SCARCITY")] = 1.0

    # ---- IMF-informed forcing variables ------------------------------
    # Fuel-subsidy pressure: IMF Box 1 — direct cost 3.9% GDP (2024) rising with parallel FX
    # IMF footnote 8: fuel subsidies would rise by 2.6 pp of GDP under devaluation
    # Calibrated path: partial-devaluation pass-through
    FUEL_SUB_EXTRA = {2025: 0.010, 2026: 0.020, 2027: 0.025}  # pp GDP above 2024
    for y, v in FUEL_SUB_EXTRA.items():
        d.loc[y, c("FUEL_SUB_EXTRA")] = v
    for y in d.index[d.index <= LAST_HIST]:
        d.loc[y, c("FUEL_SUB_EXTRA")] = 0.0

    # Hydrocarbon VA decline: IMF Text Table 3 natural gas exports 3.3% (2024) → 1.8% (2026) → declining
    # Implies volume decline of ~15%/yr for gas component
    for y in FORECAST:
        d.loc[y, c("GAS_VOL_GR")] = -0.15  # will be applied to 20% of real exports
    for y in d.index[d.index <= LAST_HIST]:
        d.loc[y, c("GAS_VOL_GR")] = 0.0

    d.to_csv(OUT)
    print(f"Extended to {d.index.max()} -> {OUT}")
    print("\nForecast exogenous path:")
    cols = [c("PANUSATLS"), c("FMLBLPOLYFR"), c("NYGDPTFP"),
            c("LMEMPSTRL"), c("XMKT_USD"), c("FIRESGRSCD"),
            c("RES_SCARCITY"), c("FUEL_SUB_EXTRA"), c("GAS_VOL_GR")]
    print(d.loc[2023:2027, cols].round(3).T.to_string())

if __name__ == "__main__":
    main()
