"""
Step 4: Extend exogenous variables 2025-2027.
Following WPS8965 convention: exogenous inputs for the forecast period.

Bolivia-specific assumptions (2026-2027 baseline):
- FX:  BOB/USD pegged at 6.96 (official) -- despite 2024 parallel market stress, official rate held
- Policy rate (lending): hold at 2024 value (~8.5%)
- Population: UN median variant, ~1.1% CAGR
- World demand (XMKT proxy): 3% real growth (IMF WEO Oct 2025 world growth)
- World prices: 2% USD inflation
- Trend TFP: extend at average growth 2014-2024 (declining productivity era)
- Structural LFPR / UNR: hold at 2024 level (paper convention)
- Oil/gas output: decline 3%/year (Bolivia gas field decline)

Output: Rawdata/bol_data_extended.csv with 2025-2027 rows (exog only).
"""
import os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "Rawdata", "bol_data.csv")
OUT  = os.path.join(ROOT, "Rawdata", "bol_data_extended.csv")

CTY = "BOL"
def c(x): return f"{CTY}{x}"

FORECAST = [2025, 2026, 2027]
LAST_HIST = 2024

EXOG_GROWTH = {
    # Bolivia maintains the official peg
    c("PANUSATLS"):    0.00,
    # Policy/lending rate flat
    c("FMLBLPOLYFR"):  0.00,
    # Population ~1.1% (UN WPP 2024 median)
    c("SPPOPTOTL"):    0.011,
    c("SPPOP1564TO"):  0.013,
    c("SPPOPWORK"):    0.013,
    # Structural labor variables flat (paper convention)
    c("LMPRTSTRL_"):   0.00,
    c("LMUNRSTRL_"):   0.00,
    # Trend TFP: use average 2014-2024 growth
    c("NYGDPTFP"):     None,   # computed from history
    # Inventories & statistical discrepancy: held at 2024 levels
    c("NEGDISTKBKN"):  0.00,
    c("NEGDISTKBCN"):  0.03,   # nominal grows with inflation
    c("NYGDPDISCKN"):  0.00,
    # Fiscal exogenous items: capital grants etc held flat
}

def main():
    d = pd.read_csv(DATA, index_col="year")
    d.index = d.index.astype(int)

    # Add forecast rows
    for y in FORECAST:
        if y not in d.index:
            d.loc[y] = pd.NA
    d = d.sort_index()

    # ---- Extend trend TFP with historical CAGR 2014-2024 -------------------
    tfp = d[c("NYGDPTFP")].dropna()
    if len(tfp) >= 2 and 2014 in tfp.index and 2024 in tfp.index:
        g_tfp = (tfp.loc[2024] / tfp.loc[2014]) ** (1 / 10) - 1
    else:
        g_tfp = -0.005
    EXOG_GROWTH[c("NYGDPTFP")] = g_tfp
    print(f"Trend TFP growth 2014-2024: {g_tfp*100:.2f}% -> extending at this rate")

    # ---- Apply simple growth-rate extensions -----------------------------
    for col, g in EXOG_GROWTH.items():
        if col not in d.columns or pd.isna(d.loc[LAST_HIST, col]):
            continue
        last = d.loc[LAST_HIST, col]
        for i, y in enumerate(FORECAST, start=1):
            d.loc[y, col] = last * (1 + g) ** i

    # ---- Structural employment (equation 1 from WPS8965) ------------------
    for y in FORECAST:
        wap    = d.loc[y, c("SPPOP1564TO")]
        lfpr_s = d.loc[y, c("LMPRTSTRL_")]
        unr_s  = d.loc[y, c("LMUNRSTRL_")]
        d.loc[y, c("LMEMPSTRL")] = wap * lfpr_s/100 * (1 - unr_s/100)
        # LF extended with participation trend (not structural)
        d.loc[y, c("LMPRTTOTL_")] = d.loc[LAST_HIST, c("LMPRTTOTL_")]
        d.loc[y, c("LMLBFTOTL")] = wap * d.loc[y, c("LMPRTTOTL_")] / 100

    # ---- World/external proxy variables ----------------------------------
    # XMKT proxy was BOL nominal GDP USD * 1.5; for forecast use 3% real + 2% price
    # But simpler: create an explicit XMKT series growing at 5% nominal USD
    last_xmkt = d.loc[LAST_HIST, c("NYGDPMKTPCD")] * 1.5
    for i, y in enumerate(FORECAST, start=1):
        d.loc[y, c("XMKT_USD")] = last_xmkt * (1.05) ** i
    # Back-fill historical XMKT proxy
    for y in d.index[d.index <= LAST_HIST]:
        d.loc[y, c("XMKT_USD")] = d.loc[y, c("NYGDPMKTPCD")] * 1.5

    # ---- Exogenous fiscal policy assumptions ------------------------------
    # BOL fiscal stance 2026-2027: assume revenue effective rate held constant
    # (business-as-usual per WPS8965 guidance); spending grows with nominal GDP.
    # These will be solved dynamically in step 5; here just ensure tax rates carried
    # Effective rates in 2024:
    rev_ratio_2024 = d.loc[LAST_HIST, c("GGREVTOTLCN")] / d.loc[LAST_HIST, c("NYGDPMKTPCN")]
    exp_ratio_2024 = d.loc[LAST_HIST, c("GGEXPTOTLCN")] / d.loc[LAST_HIST, c("NYGDPMKTPCN")]
    print(f"2024 rev/GDP = {rev_ratio_2024*100:.1f}%, exp/GDP = {exp_ratio_2024*100:.1f}%")

    d.to_csv(OUT)
    print(f"\nWrote {OUT} extended to {d.index.max()}")
    print("\nExogenous path (2024-2027):")
    exog_cols = [c("PANUSATLS"), c("FMLBLPOLYFR"), c("SPPOPTOTL"),
                 c("LMEMPSTRL"), c("NYGDPTFP"), c("XMKT_USD")]
    print(d.loc[2024:2027, exog_cols].T.to_string())

if __name__ == "__main__":
    main()
