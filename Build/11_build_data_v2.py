"""
MFMod-BOL v2 — Data layer.
Improvements over v1:
  - Long SPNF fiscal history (1990-2022) from BolBudget replaces WDI fiscal (2007 cutoff).
  - Splice 2023-2024 from BolBudget SPNF aggregates.
  - Corrects 2024 real GDP to BCB authorities nowcast (+1.3%, IMF CR 25/116 p.3).
  - Integrates bcb_financing series (monetary financing of deficit) for CPI channel.
  - Adds reserves series for reserve-scarcity indicator.
  - NFPS debt perimeter (GG + SOEs) ~ +10pp of GDP vs GG-only.
"""
import os, json
import numpy as np
import pandas as pd

ROOT = "/Users/whl/Documents/whl.BolBudget/MFMOD_BOL"
RAW  = os.path.join(ROOT, "Rawdata", "bol_raw.csv")  # WDI pull from step 01
SPNF_LONG = "/Users/whl/Documents/whl.BolBudget/analysis/spnf_long_1990_2022.csv"
SPNF_NEW  = "/Users/whl/Documents/whl.BolBudget/analysis/spnf_aggregates.csv"
TAX_LONG  = "/Users/whl/Documents/whl.BolBudget/analysis/taxes_by_type_1987_2022.csv"
OUT  = os.path.join(ROOT, "Rawdata", "bol_data_v2.csv")

ALPHA = 0.55
DEPR  = 0.05
CTY = "BOL"
def c(x): return f"{CTY}{x}"

def hp_filter(s, lam=100.0):
    from statsmodels.tsa.filters.hp_filter import hpfilter
    sd = s.dropna()
    if len(sd) < 5: return s * np.nan
    _, tr = hpfilter(sd, lamb=lam)
    return tr.reindex(s.index)

def main():
    d = pd.read_csv(RAW, index_col="year")
    d.index = d.index.astype(int)

    # ==================================================================
    # 1. Correct 2024 real GDP to BCB nowcast (+1.3% per IMF CR 25/116)
    # ==================================================================
    # WDI had BOLNYGDPMKTPKN 2024 = -1.1% vs 2023. Authorities: +1.3%.
    # Rescale all 2024 real quantities proportionally so identity holds.
    scale_24 = 1.013 * d.loc[2023, c("NYGDPMKTPKN")] / d.loc[2024, c("NYGDPMKTPKN")]
    print(f"2024 real GDP scaling factor (to BCB authorities): {scale_24:.4f}")
    real_cols = [c("NYGDPMKTPKN"), c("NECONPRVTKN"), c("NECONGOVTKN"),
                 c("NEGDIFTOTKN"), c("NEEXPGNFSKN"), c("NEIMPGNFSKN"),
                 c("NEGDISTKBKN"), c("NVAGRTOTLKN"), c("NVINDTOTLKN"),
                 c("NVSRVTOTLKN"), c("NYGDPDISCKN")]
    for col in real_cols:
        if col in d.columns:
            d.loc[2024, col] = d.loc[2024, col] * scale_24

    # ==================================================================
    # 2. Public investment / private split — keep approximation
    # ==================================================================
    d[c("NEGDIFGOVKN")] = 0.40 * d[c("NEGDIFTOTKN")]
    d[c("NEGDIFPRVKN")] = 0.60 * d[c("NEGDIFTOTKN")]
    d[c("NEGDIFGOVCN")] = 0.40 * d[c("NEGDIFTOTCN")]
    d[c("NEGDIFPRVCN")] = 0.60 * d[c("NEGDIFTOTCN")]

    # ==================================================================
    # 3. Factor cost / indirect taxes / deflators
    # ==================================================================
    d[c("NYGDPFCSTKN")] = d[c("NVAGRTOTLKN")] + d[c("NVINDTOTLKN")] + d[c("NVSRVTOTLKN")]
    d[c("NYGDPFCSTCN")] = d[c("NVAGRTOTLCN")] + d[c("NVINDTOTLCN")] + d[c("NVSRVTOTLCN")]
    d[c("NYTAXNINDKN")] = d[c("NYGDPMKTPKN")] - d[c("NYGDPFCSTKN")]
    d[c("NYTAXNINDCN")] = d[c("NYGDPMKTPCN")] - d[c("NYGDPFCSTCN")]

    for base, num, den in [
        (c("NYGDPMKTPXN"), c("NYGDPMKTPCN"), c("NYGDPMKTPKN")),
        (c("NYGDPFCSTXN"), c("NYGDPFCSTCN"), c("NYGDPFCSTKN")),
        (c("NECONPRVTXN"), c("NECONPRVTCN"), c("NECONPRVTKN")),
        (c("NECONGOVTXN"), c("NECONGOVTCN"), c("NECONGOVTKN")),
        (c("NEGDIFTOTXN"), c("NEGDIFTOTCN"), c("NEGDIFTOTKN")),
        (c("NEEXPGNFSXN"), c("NEEXPGNFSCN"), c("NEEXPGNFSKN")),
        (c("NEIMPGNFSXN"), c("NEIMPGNFSCN"), c("NEIMPGNFSKN")),
        (c("NVAGRTOTLXN"), c("NVAGRTOTLCN"), c("NVAGRTOTLKN")),
        (c("NVINDTOTLXN"), c("NVINDTOTLCN"), c("NVINDTOTLKN")),
        (c("NVSRVTOTLXN"), c("NVSRVTOTLCN"), c("NVSRVTOTLKN"))]:
        d[base] = d[num] / d[den]

    # ==================================================================
    # 4. Labor market
    # ==================================================================
    d[c("LMLBFTOTL")] = d[c("SPPOP1564TO")] * d[c("LMPRTTOTL_")] / 100
    d[c("LMEMPTOTL")] = d[c("LMLBFTOTL")] * (1 - d[c("LMUNRTOTL_")] / 100)
    d[c("SPPOPWORK")] = d[c("SPPOP1564TO")] * 1.15
    d[c("NYYWBTOTLCN")] = ALPHA * d[c("NYGDPFCSTCN")]
    d[c("NEWRTTOTLXN")] = d[c("NYYWBTOTLCN")] / d[c("LMEMPTOTL")]

    # ==================================================================
    # 5. Long SPNF fiscal (1990-2022) -> MFMod series
    # ==================================================================
    long = pd.read_csv(SPNF_LONG, index_col="rubro").T
    long.index = long.index.astype(int)
    # Units: MM Bs nominal -> Bs
    M = 1e6
    # Splice 2023-2024 from shorter series
    recent = pd.read_csv(SPNF_NEW).set_index("year")
    long2 = long.copy()
    for y in [2023, 2024]:
        if y in recent.index:
            for col in long2.columns:
                if col in recent.columns:
                    long2.loc[y, col] = recent.loc[y, col]
    # BCB financing: only in 1990-2022 series; extrapolate 2023-24
    if "bcb_financing" in long2.columns:
        # 2022: 7482 MM Bs; 2023 & 2024 per BCB monetary operations (IMF para 9: ~5% GDP monetization)
        # IMF Text Table 3: monetary financing lines implied ~10% of GDP for 2024
        if 2023 not in long.index or pd.isna(long2.loc[2023, "bcb_financing"]):
            # Extrapolate: 2023 ~ 10% of GDP, 2024 ~ 11%
            nom_gdp_22 = d.loc[2022, c("NYGDPMKTPCN")] / M
            long2.loc[2023, "bcb_financing"] = 0.10 * d.loc[2023, c("NYGDPMKTPCN")] / M
            long2.loc[2024, "bcb_financing"] = 0.11 * d.loc[2024, c("NYGDPMKTPCN")] / M

    # Map to MFMod (and multiply by M to get Bs)
    fmap = {
        "income_total":  c("GGREVTOTLCN"),
        "tax_total":     c("GGREVTAXTCN"),
        "exp_total":     c("GGEXPTOTLCN"),
        "exp_current":   c("GGEXPCRNTCN"),
        "wages":         c("GGEXPWAGECN"),
        "goods_services":c("GGEXPGNFSCN"),
        "int_ext_debt":  c("GGEXPINTECN"),
        "int_int_debt":  c("GGEXPINTDCN"),
        "capital_exp":   c("GGEXPCAPTCN"),
        "global_balance":c("GGBALOVRLCN"),
        "primary_balance":c("GGBALPRIMCN"),
        "transfers_paid":c("GGEXPTRNSCN"),
        "hydrocarbons_rev":c("GGREVHYDRCN"),
        "tax_hydroc_spnf":c("GGREVTAXHCN"),
        "bcb_financing": c("GGFINBCBCN"),  # monetary financing series
        "ext_credit_net":c("GGFINEXTNCN"),
        "int_credit_net":c("GGFINDOMNCN"),
    }
    for src, dst in fmap.items():
        if src in long2.columns:
            if dst not in d.columns:
                d[dst] = np.nan
            for y in long2.index:
                if y in d.index and pd.notna(long2.loc[y, src]):
                    d.loc[y, dst] = long2.loc[y, src] * M
    # Derived: total interest
    d[c("GGEXPINTPCN")] = d[c("GGEXPINTECN")].fillna(0) + d[c("GGEXPINTDCN")].fillna(0)
    # Direct/indirect split
    d[c("GGREVDRCTCN")] = 0.28 * d[c("GGREVTAXTCN")]
    d[c("GGREVIDRTCN")] = 0.72 * d[c("GGREVTAXTCN")]

    # ==================================================================
    # 6. Debt stock — NFPS perimeter (IMF Art IV path)
    # ==================================================================
    nfps_debt_gdp = {
        1994: 65.0, 1995: 68.0, 1996: 64.0, 1997: 61.0, 1998: 64.0, 1999: 71.0,
        2000: 78.0, 2001: 74.0, 2002: 81.0, 2003: 94.0, 2004: 92.0, 2005: 79.0,
        2006: 54.0, 2007: 42.0, 2008: 39.0, 2009: 44.0, 2010: 41.0, 2011: 37.0,
        2012: 36.0, 2013: 38.0, 2014: 44.0, 2015: 49.0, 2016: 54.0, 2017: 59.0,
        2018: 61.0, 2019: 64.0, 2020: 85.0, 2021: 90.0, 2022: 88.0, 2023: 90.8,
        2024: 95.0,  # IMF Art IV CR 25/116 Table 1
    }
    d[c("GGDBTTOTLGD")] = pd.Series(nfps_debt_gdp).reindex(d.index)
    d[c("GGDBTTOTLCN")] = d[c("GGDBTTOTLGD")] / 100 * d[c("NYGDPMKTPCN")]
    # External fraction: IMF shows external falling from 30% to 18% of GDP (peg-valued)
    ext_share = {1994:0.85, 2000:0.80, 2010:0.60, 2015:0.45, 2020:0.40,
                 2023: 29.9/90.8, 2024: 27.6/95.0}  # IMF Art IV ratios
    ext_share_s = pd.Series(ext_share).reindex(d.index).interpolate()
    d[c("GGDBTEXTLCN")] = ext_share_s * d[c("GGDBTTOTLCN")] / (d[c("GGDBTTOTLGD")] / 100 * d[c("NYGDPMKTPCN")]) * \
                          d[c("GGDBTTOTLCN")]
    d[c("GGDBTEXTLCN")] = ext_share_s * d[c("GGDBTTOTLGD")] / 100 * d[c("NYGDPMKTPCN")]
    d[c("GGDBTDOMTCN")] = d[c("GGDBTTOTLCN")] - d[c("GGDBTEXTLCN")]

    # ==================================================================
    # 7. Reserves (proxy for scarcity indicator)
    # ==================================================================
    # IMF path (USD millions gross IR): from Table 1 CR 25/116
    res_path = {
        2010: 9729, 2011:12019, 2012:13927, 2013:14430, 2014:15123, 2015:13056,
        2016:10081, 2017:10261, 2018: 8946, 2019: 6468, 2020: 5275, 2021: 4752,
        2022: 3796, 2023: 1808, 2024: 2009,
    }
    d[c("FIRESGRSCD")] = pd.Series(res_path).reindex(d.index)
    # Months of imports cover
    imp_usd = d[c("NEIMPGNFSCN")] / d[c("PANUSATLS")] / 12
    d[c("FIRESMONTHS")] = d[c("FIRESGRSCD")] * 1e6 / imp_usd
    # Reserve-scarcity indicator: 0 when reserves >= 6 months, 1 when <= 2 months
    rs = d[c("FIRESMONTHS")]
    d[c("RES_SCARCITY")] = np.clip((6 - rs) / 4, 0, 1).fillna(0)

    # ==================================================================
    # 8. Capital stock (perpetual inventory)
    # ==================================================================
    I = d[c("NEGDIFTOTKN")].dropna()
    Y = d[c("NYGDPMKTPKN")].dropna()
    common = I.index.intersection(Y.index)
    I, Y = I.loc[common], Y.loc[common]
    t_max = 15
    if len(I) >= t_max + 1:
        y0 = I.index.min()
        yt = y0 + t_max
        num = sum((1 - DEPR) ** (t_max - i) * I.iloc[i] for i in range(1, t_max + 1))
        den = (Y.loc[yt] / Y.loc[y0]) - (1 - DEPR) ** t_max
        K0 = num / den if den > 0 else Y.iloc[0] * 3
    else:
        K0 = Y.iloc[0] * 3

    K = pd.Series(index=Y.index, dtype=float)
    K.iloc[0] = K0
    for i in range(1, len(Y)):
        K.iloc[i] = (1 - DEPR) * K.iloc[i-1] + I.iloc[i]
    d[c("NEGDIKSTKKN")] = K.reindex(d.index)

    # ==================================================================
    # 9. Trend TFP, potential GDP, output gap
    # ==================================================================
    L = d[c("LMEMPTOTL")]
    A = Y / (K.pow(1 - ALPHA) * L.reindex(Y.index).pow(ALPHA))
    d[c("NYGDPTFP_ACT")] = A.reindex(d.index)
    d[c("LMPRTSTRL_")] = hp_filter(d[c("LMPRTTOTL_")], lam=100)
    d[c("LMUNRSTRL_")] = hp_filter(d[c("LMUNRTOTL_")],  lam=100)
    d[c("LMEMPSTRL")] = d[c("SPPOP1564TO")] * d[c("LMPRTSTRL_")]/100 * \
                       (1 - d[c("LMUNRSTRL_")]/100)
    d[c("NYGDPTFP")] = hp_filter(A, lam=100).reindex(d.index)
    Kl1 = d[c("NEGDIKSTKKN")].shift(1)
    d[c("NYGDPPOTLKN")] = (d[c("NYGDPTFP")] *
                          d[c("LMEMPSTRL")].pow(ALPHA) *
                          Kl1.pow(1 - ALPHA))
    d[c("NYGDPGAP_")] = (d[c("NYGDPMKTPKN")] / d[c("NYGDPPOTLKN")] - 1) * 100

    # ==================================================================
    # 10. Fiscal ratios & summary
    # ==================================================================
    d[c("GGREVTOTLGD")] = d[c("GGREVTOTLCN")] / d[c("NYGDPMKTPCN")] * 100
    d[c("GGEXPTOTLGD")] = d[c("GGEXPTOTLCN")] / d[c("NYGDPMKTPCN")] * 100
    d[c("GGBALOVRLGD")] = d[c("GGBALOVRLCN")] / d[c("NYGDPMKTPCN")] * 100
    d[c("GGFINBCBGD")]  = d[c("GGFINBCBCN")]  / d[c("NYGDPMKTPCN")] * 100

    d.to_csv(OUT)
    print(f"Wrote {OUT} with {d.shape[1]} columns, {d.shape[0]} years")
    print("\nLong SPNF coverage check (2010-2024):")
    qa = [c("NYGDPMKTPKN"), c("NYGDPGAP_"), c("GGREVTOTLGD"),
          c("GGEXPTOTLGD"), c("GGBALOVRLGD"),
          c("GGFINBCBGD"), c("GGDBTTOTLGD"),
          c("FIRESMONTHS"), c("RES_SCARCITY")]
    print(d.loc[2010:2024, qa].round(2).T.to_string())

if __name__ == "__main__":
    main()
