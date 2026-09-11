"""
Step 2: Organize raw data into MFMod variable panel and derive series.
- Merge WDI with local BolBudget fiscal database (2017-2024, MM Bs nominal).
- Derive employment from labor force and unemployment rate.
- Compute capital stock (perpetual inventory, WPS8965 Box 1).
- Compute trend TFP (HP filter, lambda=100) and potential GDP (Cobb-Douglas).
- Compute output gap.
Output: Rawdata/bol_data.csv (historical panel, MFMod names).
"""
import os
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW  = os.path.join(ROOT, "Rawdata", "bol_raw.csv")
FISC = "/Users/whl/Documents/whl.BolBudget/analysis/spnf_aggregates.csv"
OUT  = os.path.join(ROOT, "Rawdata", "bol_data.csv")

CTY = "BOL"
def c(x): return f"{CTY}{x}"

# WPS8965 Box 1 constants
DEPR  = 0.05   # depreciation rate (5%, standard for developing countries)
ALPHA = 0.55   # labor share of income (Penn World Tables ~0.55 for BOL)

def hp_filter(series: pd.Series, lam: float = 100.0) -> pd.Series:
    """Hodrick-Prescott filter. lambda=100 for annual data."""
    from statsmodels.tsa.filters.hp_filter import hpfilter
    s = series.dropna()
    if len(s) < 5:
        return series * np.nan
    _, trend = hpfilter(s, lamb=lam)
    return trend.reindex(series.index)

def main():
    d = pd.read_csv(RAW, index_col="year")
    d.index = d.index.astype(int)

    # ------------------------------------------------------------------
    # 1. GDP identities / fill missing columns
    # ------------------------------------------------------------------
    # Real private investment = real total - public (public is mostly in fiscal)
    # WDI doesn't split public/private GDIF reliably for BOL; approximate via share
    # BOL historical: public investment ~40% of total GDIF
    d[c("NEGDIFGOVKN")] = 0.40 * d[c("NEGDIFTOTKN")]
    d[c("NEGDIFPRVKN")] = 0.60 * d[c("NEGDIFTOTKN")]
    d[c("NEGDIFGOVCN")] = 0.40 * d[c("NEGDIFTOTCN")]
    d[c("NEGDIFPRVCN")] = 0.60 * d[c("NEGDIFTOTCN")]

    # GDP at factor cost (production side, real and nominal)
    d[c("NYGDPFCSTKN")] = d[c("NVAGRTOTLKN")] + d[c("NVINDTOTLKN")] + d[c("NVSRVTOTLKN")]
    d[c("NYGDPFCSTCN")] = d[c("NVAGRTOTLCN")] + d[c("NVINDTOTLCN")] + d[c("NVSRVTOTLCN")]
    # Net indirect taxes (residual)
    d[c("NYTAXNINDKN")] = d[c("NYGDPMKTPKN")] - d[c("NYGDPFCSTKN")]
    d[c("NYTAXNINDCN")] = d[c("NYGDPMKTPCN")] - d[c("NYGDPFCSTCN")]

    # Deflators (implicit)
    d[c("NYGDPMKTPXN")] = d[c("NYGDPMKTPCN")] / d[c("NYGDPMKTPKN")]
    d[c("NYGDPFCSTXN")] = d[c("NYGDPFCSTCN")] / d[c("NYGDPFCSTKN")]
    d[c("NECONPRVTXN")] = d[c("NECONPRVTCN")] / d[c("NECONPRVTKN")]
    d[c("NECONGOVTXN")] = d[c("NECONGOVTCN")] / d[c("NECONGOVTKN")]
    d[c("NEGDIFTOTXN")] = d[c("NEGDIFTOTCN")] / d[c("NEGDIFTOTKN")]
    d[c("NEEXPGNFSXN")] = d[c("NEEXPGNFSCN")] / d[c("NEEXPGNFSKN")]
    d[c("NEIMPGNFSXN")] = d[c("NEIMPGNFSCN")] / d[c("NEIMPGNFSKN")]
    d[c("NVAGRTOTLXN")] = d[c("NVAGRTOTLCN")] / d[c("NVAGRTOTLKN")]
    d[c("NVINDTOTLXN")] = d[c("NVINDTOTLCN")] / d[c("NVINDTOTLKN")]
    d[c("NVSRVTOTLXN")] = d[c("NVSRVTOTLCN")] / d[c("NVSRVTOTLKN")]

    # ------------------------------------------------------------------
    # 2. Labor market
    # ------------------------------------------------------------------
    # Labor force = pop15-64 * participation/100
    d[c("LMLBFTOTL")] = d[c("SPPOP1564TO")] * d[c("LMPRTTOTL_")] / 100
    # Employment = LF * (1 - unrate/100)
    d[c("LMEMPTOTL")] = d[c("LMLBFTOTL")] * (1 - d[c("LMUNRTOTL_")] / 100)
    # Working-age population (15+) proxy = POP1564 + ~15% for 65+
    d[c("SPPOPWORK")] = d[c("SPPOP1564TO")] * 1.15
    # Wage bill proxy = labor share × nominal GDP at factor cost
    d[c("NYYWBTOTLCN")] = ALPHA * d[c("NYGDPFCSTCN")]
    # Average nominal wage (LCU per worker per year)
    d[c("NEWRTTOTLXN")] = d[c("NYYWBTOTLCN")] / d[c("LMEMPTOTL")]

    # ------------------------------------------------------------------
    # 3. Merge BolBudget local fiscal (2017-2024, MM Bs) -> LCU units same as WDI
    # ------------------------------------------------------------------
    fisc = pd.read_csv(FISC)
    fisc = fisc.set_index("year")
    # Convert MM Bs -> Bs (multiply by 1e6) to match WDI CN units (current LCU)
    M = 1e6
    # Total revenue (MFMod: GGREVTOTLCN)
    rev = fisc["income_total"] * M
    # Tax revenue
    tax = fisc["tax_revenue"] * M
    # Total expenditure
    exp_tot = fisc["exp_total"] * M
    # Interest on external + internal debt
    int_ext = fisc["int_ext_debt"].fillna(0) * M
    int_int = fisc["int_int_debt"].fillna(0) * M
    int_tot = int_ext + int_int
    # Capital expenditure
    capx = fisc["capital_exp"].fillna(0) * M
    # Wages
    wages = fisc["wages"].fillna(0) * M
    # Goods & services
    gs = fisc["goods_services"].fillna(0) * M
    # Balance
    bal = fisc["global_balance"] * M
    # Transfers paid
    trn = fisc["transfers_paid"].fillna(0) * M

    # Fill MFMod fiscal series (override where we have local data, else keep WDI)
    def fill(col: str, series: pd.Series):
        if col not in d.columns:
            d[col] = pd.NA
        for y, v in series.dropna().items():
            if int(y) in d.index:
                d.at[int(y), col] = v

    fill(c("GGREVTOTLCN"), rev)
    fill(c("GGREVTAXTCN"), tax)
    fill(c("GGEXPTOTLCN"), exp_tot)
    fill(c("GGEXPINTPCN"), int_tot)
    fill(c("GGEXPINTECN"), int_ext)
    fill(c("GGEXPINTDCN"), int_int)
    fill(c("GGEXPCAPTCN"), capx)
    fill(c("GGEXPWAGECN"), wages)
    fill(c("GGEXPGNFSCN"), gs)
    fill(c("GGBALOVRLCN"), bal)
    fill(c("GGEXPTRNSCN"), trn)

    # Direct vs indirect taxes (BolBudget has a detailed tax_by_type.csv; use rough split)
    # For ECM estimation we need historical split; use WDI GC.TAX as fallback pre-2017
    # Direct taxes BOL: IUE + RC-IVA + ITF + IEHD direct ~ 28% of tax rev
    # Indirect: IVA MI + IVA Imp + IT + ICE + GA ~ 72% of tax rev
    d[c("GGREVDRCTCN")] = 0.28 * d[c("GGREVTAXTCN")]
    d[c("GGREVIDRTCN")] = 0.72 * d[c("GGREVTAXTCN")]

    # Debt stock: WDI has % GDP only up to ~2001. Use BCB-reported path:
    # BOL public debt ~38% 2014 -> 62% 2019 -> 85% 2024 (approx)
    debt_gdp_path = {
        1994: 59.2, 1995: 62.0, 1996: 58.0, 1997: 55.0, 1998: 58.0, 1999: 65.0,
        2000: 72.0, 2001: 68.3, 2002: 75.0, 2003: 88.0, 2004: 86.0, 2005: 73.0,
        2006: 48.0, 2007: 36.0, 2008: 33.0, 2009: 38.0, 2010: 35.0, 2011: 31.0,
        2012: 30.0, 2013: 32.0, 2014: 38.0, 2015: 43.0, 2016: 48.0, 2017: 53.0,
        2018: 55.0, 2019: 58.0, 2020: 79.0, 2021: 84.0, 2022: 82.0, 2023: 83.0,
        2024: 85.0,
    }
    d[c("GGDBTTOTLGD")] = pd.Series(debt_gdp_path).reindex(d.index)
    d[c("GGDBTTOTLCN")] = d[c("GGDBTTOTLGD")] / 100 * d[c("NYGDPMKTPCN")]
    # External vs domestic split (BOL ~55% external historically)
    d[c("GGDBTEXTLCN")] = 0.55 * d[c("GGDBTTOTLCN")]
    d[c("GGDBTDOMTCN")] = 0.45 * d[c("GGDBTTOTLCN")]

    # ------------------------------------------------------------------
    # 4. Capital stock (perpetual inventory method, WPS8965 Box 1)
    # ------------------------------------------------------------------
    # Solve K(0) using equation from paper:
    # K(0) = sum_{i=1..t}[(1-delta)^(t-i) * I_i] / [Y_t/Y_0 - (1-delta)^t]
    # Use a base year early in the series
    I = d[c("NEGDIFTOTKN")].dropna()
    Y = d[c("NYGDPMKTPKN")].dropna()
    common = I.index.intersection(Y.index)
    I, Y = I.loc[common], Y.loc[common]
    t_max = 15  # years to accumulate for initial estimate
    if len(I) >= t_max + 1:
        y0 = I.index.min()
        yt = y0 + t_max
        num = sum((1 - DEPR) ** (t_max - i) * I.iloc[i] for i in range(1, t_max + 1))
        den = (Y.loc[yt] / Y.loc[y0]) - (1 - DEPR) ** t_max
        K0 = num / den if den > 0 else Y.iloc[0] * 3
    else:
        K0 = Y.iloc[0] * 3  # fallback: K/Y=3

    # Roll forward capital stock from first year of data
    K = pd.Series(index=Y.index, dtype=float)
    K.iloc[0] = K0
    for i in range(1, len(Y)):
        K.iloc[i] = (1 - DEPR) * K.iloc[i-1] + I.iloc[i]
    d[c("NEGDIKSTKKN")] = K.reindex(d.index)

    # ------------------------------------------------------------------
    # 5. Trend TFP (HP filter) and potential GDP
    # ------------------------------------------------------------------
    # Instantaneous TFP: A = Y / (K^(1-alpha) * L^alpha)
    L = d[c("LMEMPTOTL")]
    A = Y / (K.pow(1 - ALPHA) * L.reindex(Y.index).pow(ALPHA))
    d[c("NYGDPTFP_ACT")] = A.reindex(d.index)
    # Structural employment L* = WAP * equilibrium participation * (1-u*)
    lfpr_star = hp_filter(d[c("LMPRTTOTL_")], lam=100)
    unrt_star = hp_filter(d[c("LMUNRTOTL_")],  lam=100)
    d[c("LMPRTSTRL_")] = lfpr_star
    d[c("LMUNRSTRL_")] = unrt_star
    d[c("LMEMPSTRL")] = d[c("SPPOP1564TO")] * lfpr_star/100 * (1 - unrt_star/100)

    # Trend TFP via HP
    A_trend = hp_filter(A, lam=100)
    d[c("NYGDPTFP")] = A_trend.reindex(d.index)

    # Potential GDP = A_trend * L*^alpha * K(-1)^(1-alpha)
    Kl1 = d[c("NEGDIKSTKKN")].shift(1)
    d[c("NYGDPPOTLKN")] = (d[c("NYGDPTFP")] *
                          d[c("LMEMPSTRL")].pow(ALPHA) *
                          Kl1.pow(1 - ALPHA))
    # Output gap
    d[c("NYGDPGAP_")] = (d[c("NYGDPMKTPKN")] / d[c("NYGDPPOTLKN")] - 1) * 100

    # ------------------------------------------------------------------
    # 6. Save
    # ------------------------------------------------------------------
    d.to_csv(OUT)
    print(f"Wrote {OUT} with {d.shape[1]} columns, {d.shape[0]} years")
    # Report critical columns for QA
    qa = [c("NYGDPMKTPKN"), c("NYGDPPOTLKN"), c("NYGDPGAP_"),
          c("LMEMPTOTL"), c("LMEMPSTRL"), c("NYGDPTFP"),
          c("NEGDIKSTKKN"), c("GGREVTOTLCN"), c("GGEXPTOTLCN"),
          c("GGBALOVRLCN"), c("GGDBTTOTLCN")]
    print("\nQA (latest 5 years):")
    print(d[qa].tail(5).T.to_string())

if __name__ == "__main__":
    main()
