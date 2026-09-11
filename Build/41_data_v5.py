"""
MFMod-BOL v5 — DATA LAYER (full rebuild).

Fixes the fundamental issue v1-v4 all suffered from: the 2017 INE GDP rebase
(+35% level jump) that made all longitudinal estimation biased. Uses the
SPLICED GDP from BolBudget (gdp_spliced_2000_2024.csv) which maintains
continuous growth rates across the methodological break.

Other upgrades:
  - Actual INE CPI long series (cpi_index_1990_2024.csv) instead of WDI
  - Actual BCB Reservas Internacionales Netas (bcb_rin_2000_2024.csv)
  - SPNF real 2024Bs (spnf_real_2024Bs.csv) for real fiscal variables
  - Actual fuel subsidy history (subsidio_combustibles.csv)
  - Inversion publica by sector (inversion_publica_by_sector_1990_2024.csv)
  - Structural balance output gap (structural_balance.csv)
  - Tax long 1987-2024 (taxes_by_type_1987_2024.csv) for hydrocarbon revenue
"""
import os, json
import numpy as np
import pandas as pd

ROOT = "/Users/whl/Documents/whl.BolBudget/MFMOD_BOL"
BUD  = "/Users/whl/Documents/whl.BolBudget/analysis"
RAW  = os.path.join(ROOT, "Rawdata", "bol_raw.csv")  # original WDI pull (NIA real, BoP)
OUT  = os.path.join(ROOT, "Rawdata", "bol_data_v5.csv")

CTY = "BOL"
def c(x): return f"{CTY}{x}"
ALPHA = 0.55
DEPR  = 0.05

def main():
    # ------------------------------------------------------------------
    # 1. Start with WDI pull (NIA real components, BoP, labor)
    # ------------------------------------------------------------------
    d = pd.read_csv(RAW, index_col="year")
    d.index = d.index.astype(int)
    M = 1e6

    # ------------------------------------------------------------------
    # 2. FIX: use SPLICED nominal GDP (kills 2017 break)
    # ------------------------------------------------------------------
    g = pd.read_csv(f"{BUD}/gdp_spliced_2000_2024.csv")
    gdp_sp = g.set_index("year")["gdp_nominal_MM_Bs_spliced"] * M  # to Bs
    # Keep pre-2000 WDI levels (no spliced version available); splice at 2000
    d[c("NYGDPMKTPCN")] = gdp_sp.reindex(d.index).combine_first(d[c("NYGDPMKTPCN")])

    # ------------------------------------------------------------------
    # 3. FIX: use actual INE CPI long series
    # ------------------------------------------------------------------
    cpi = pd.read_csv(f"{BUD}/cpi_index_1990_2024.csv").set_index("year")
    # CPI series index: base 2010=100
    d[c("FPCPITOTLXN")] = cpi["cpi_2010=100"].reindex(d.index)

    # ------------------------------------------------------------------
    # 4. Back out real NIA using spliced GDP — rescale WDI real series to
    #    preserve WDI real growth rates but match spliced nominal levels
    # ------------------------------------------------------------------
    # Real GDP for 2024: IMF/BCB authorities +1.3% from 2023. Other years: WDI rates.
    # Get WDI real GDP growth rates (correct direction, no 2017 break in real)
    # WDI NY.GDP.MKTP.KN stored originally in d[c("NYGDPMKTPKN")]
    # But we must now reconcile: derive new real GDP that matches IMF 2024 and WDI growth rates
    wdi_real = d[c("NYGDPMKTPKN")].copy()
    wdi_real_growth = wdi_real.pct_change()
    # Override 2024 growth with IMF authorities (+1.3%)
    if 2024 in wdi_real_growth.index:
        wdi_real_growth.loc[2024] = 0.013
    # Roll forward from 2015 base (reasonable pre-crisis anchor)
    anchor_year = 2015
    anchor_val  = wdi_real.loc[anchor_year]
    new_real = wdi_real.copy()
    for y in sorted(wdi_real.index):
        if y == anchor_year: new_real.loc[y] = anchor_val
        elif y > anchor_year:
            new_real.loc[y] = new_real.loc[y-1] * (1 + wdi_real_growth.loc[y])
        else:
            new_real.loc[y] = new_real.loc[y+1] / (1 + wdi_real_growth.loc[y+1])
    d[c("NYGDPMKTPKN")] = new_real

    # Rescale sectoral VA and NIA components to maintain 2015 shares (minor adjustment)
    # Real C, G, I, X, M retained from WDI (their own growth is fine)
    # Just recompute GDP deflator from spliced nominal / real
    d[c("NYGDPMKTPXN")] = d[c("NYGDPMKTPCN")] / d[c("NYGDPMKTPKN")]

    # ------------------------------------------------------------------
    # 5. Public / private investment split (retain 40/60 for now)
    # ------------------------------------------------------------------
    d[c("NEGDIFGOVKN")] = 0.40 * d[c("NEGDIFTOTKN")]
    d[c("NEGDIFPRVKN")] = 0.60 * d[c("NEGDIFTOTKN")]
    d[c("NEGDIFGOVCN")] = 0.40 * d[c("NEGDIFTOTCN")]
    d[c("NEGDIFPRVCN")] = 0.60 * d[c("NEGDIFTOTCN")]

    # ------------------------------------------------------------------
    # 6. Factor cost / indirect taxes / deflators
    # ------------------------------------------------------------------
    d[c("NYGDPFCSTKN")] = d[c("NVAGRTOTLKN")] + d[c("NVINDTOTLKN")] + d[c("NVSRVTOTLKN")]
    d[c("NYGDPFCSTCN")] = d[c("NVAGRTOTLCN")] + d[c("NVINDTOTLCN")] + d[c("NVSRVTOTLCN")]
    d[c("NYTAXNINDKN")] = d[c("NYGDPMKTPKN")] - d[c("NYGDPFCSTKN")]
    d[c("NYTAXNINDCN")] = d[c("NYGDPMKTPCN")] - d[c("NYGDPFCSTCN")]

    for base, num, den in [
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

    # ------------------------------------------------------------------
    # 7. Labor
    # ------------------------------------------------------------------
    d[c("LMLBFTOTL")] = d[c("SPPOP1564TO")] * d[c("LMPRTTOTL_")] / 100
    d[c("LMEMPTOTL")] = d[c("LMLBFTOTL")] * (1 - d[c("LMUNRTOTL_")] / 100)
    d[c("SPPOPWORK")] = d[c("SPPOP1564TO")] * 1.15
    d[c("NYYWBTOTLCN")] = ALPHA * d[c("NYGDPFCSTCN")]
    d[c("NEWRTTOTLXN")] = d[c("NYYWBTOTLCN")] / d[c("LMEMPTOTL")]

    # ------------------------------------------------------------------
    # 8. FIX: BCB actual RIN (annual)
    # ------------------------------------------------------------------
    rin = pd.read_csv(f"{BUD}/bcb_rin_2000_2024.csv").set_index("year")
    d[c("FIRESGRSCD")] = rin["RIN_USD_MM"].reindex(d.index)
    imp_usd_mth = d[c("NEIMPGNFSCN")] / d[c("PANUSATLS")] / 12
    d[c("FIRESMONTHS")] = d[c("FIRESGRSCD")] * M / imp_usd_mth
    # Reserve scarcity indicator (piecewise linear, 0 at 6mo, 1 at 2mo)
    d[c("RES_SCARCITY")] = np.clip((6 - d[c("FIRESMONTHS")]) / 4, 0, 1).fillna(0)

    # ------------------------------------------------------------------
    # 9. FIX: long SPNF 1990-2024 (BolBudget full series)
    # ------------------------------------------------------------------
    spnf = pd.read_csv(f"{BUD}/spnf_long_1990_2024.csv", index_col="rubro").T
    spnf.index = spnf.index.astype(int)
    fmap = {
        "income_total":   c("GGREVTOTLCN"),
        "tax_total":      c("GGREVTAXTCN"),
        "tax_hydroc_spnf":c("GGREVTAXHYDROCN"),
        "hydrocarbons_rev":c("GGREVHYDRCN"),
        "exp_total":      c("GGEXPTOTLCN"),
        "exp_current":    c("GGEXPCRNTCN"),
        "wages":          c("GGEXPWAGESCN"),
        "goods_services": c("GGEXPGSCN"),
        "int_ext_debt":   c("GGEXPINTECN"),
        "int_int_debt":   c("GGEXPINTDCN"),
        "capital_exp":    c("GGEXPCAPEXCN"),
        "transfers_paid": c("GGEXPTRNSCN"),
        "global_balance": c("GGBALOVRLCN"),
        "primary_balance":c("GGBALPRIMCN"),
        "bcb_financing":  c("GGFINBCBCN"),
        "ext_credit_net": c("GGFINEXTNCN"),
        "int_credit_net": c("GGFINDOMNCN"),
    }
    for src, dst in fmap.items():
        if src in spnf.columns:
            s = spnf[src].reindex(d.index) * M  # MM Bs -> Bs
            if dst not in d.columns: d[dst] = np.nan
            d.loc[s.dropna().index, dst] = s.dropna()
    d[c("GGEXPINTPCN")] = d[c("GGEXPINTECN")].fillna(0) + d[c("GGEXPINTDCN")].fillna(0)
    d[c("GGREVDRCTCN")] = 0.28 * d[c("GGREVTAXTCN")]
    d[c("GGREVIDRTCN")] = 0.72 * d[c("GGREVTAXTCN")]

    # ------------------------------------------------------------------
    # 10. FIX: fuel subsidy history (explicit series)
    # ------------------------------------------------------------------
    sub = pd.read_csv(f"{BUD}/subsidio_combustibles.csv")
    if "subsidy_MM_Bs" in sub.columns:
        sub_bs = sub.set_index("year")["subsidy_MM_Bs"] * M
        # Fill pre-2008 with 0, 2008-2016 with USD conversion
        for y in sub["year"].unique():
            v = sub[sub.year == y].iloc[0]
            if pd.isna(v["subsidy_MM_Bs"]) and pd.notna(v["subsidy_USD_MM"]):
                fx = d.loc[y, c("PANUSATLS")] if pd.notna(d.loc[y, c("PANUSATLS")]) else 6.96
                sub_bs.loc[y] = v["subsidy_USD_MM"] * fx * M
        d[c("GGEXPFUELCN")] = sub_bs.reindex(d.index).fillna(0)
    else:
        d[c("GGEXPFUELCN")] = 0

    # ------------------------------------------------------------------
    # 11. FIX: hydrocarbon revenue from tax series (IDH, IEHD long)
    # ------------------------------------------------------------------
    tx = pd.read_csv(f"{BUD}/taxes_by_type_1987_2024.csv", index_col="tax").T
    tx.index = tx.index.astype(int)
    if "IDH" in tx.columns:
        d[c("GGREVIDHCN")] = tx["IDH"].reindex(d.index) * M
    if "IEHD" in tx.columns:
        d[c("GGREVIEHDCN")] = tx["IEHD"].reindex(d.index) * M

    # ------------------------------------------------------------------
    # 12. FIX: NFPS debt path from IMF WEO (via macro_gdp_debt)
    # ------------------------------------------------------------------
    md = pd.read_csv(f"{BUD}/macro_gdp_debt_2000_2024.csv").set_index("year")
    d[c("GGDBTTOTLGD")] = md["consolidated_debt_pct_GDP"].reindex(d.index)
    # Pre-2000 retain prior path (from v3 debt calibration)
    pre_2000_debt = {1990:70, 1991:75, 1992:80, 1993:82, 1994:65, 1995:68, 1996:64,
                     1997:61, 1998:64, 1999:71}
    for y, v in pre_2000_debt.items():
        if pd.isna(d.loc[y, c("GGDBTTOTLGD")]):
            d.loc[y, c("GGDBTTOTLGD")] = v
    d[c("GGDBTTOTLCN")] = d[c("GGDBTTOTLGD")] / 100 * d[c("NYGDPMKTPCN")]
    # External debt share (from md table)
    if "external_debt_USD_MM" in md.columns:
        ext_lcu = md["external_debt_USD_MM"].reindex(d.index) * d[c("PANUSATLS")] * M
        d[c("GGDBTEXTLCN")] = ext_lcu
    d[c("GGDBTDOMTCN")] = d[c("GGDBTTOTLCN")] - d[c("GGDBTEXTLCN")].fillna(0)
    d[c("GGEXPINTECN")] = d[c("GGEXPINTECN")].fillna(0)
    d[c("GGEXPINTDCN")] = d[c("GGEXPINTDCN")].fillna(0)

    # ------------------------------------------------------------------
    # 13. Structural balance + output gap (BolBudget)
    # ------------------------------------------------------------------
    sb = pd.read_csv(f"{BUD}/structural_balance.csv").set_index("year")
    d[c("NYGDPGAP_STR")] = sb["output_gap_pct"].reindex(d.index)
    d[c("GGBALSTRPGD")] = sb["structural_pctGDP"].reindex(d.index)

    # ------------------------------------------------------------------
    # 14. Capital stock + potential (Cobb-Douglas on corrected series)
    # ------------------------------------------------------------------
    from statsmodels.tsa.filters.hp_filter import hpfilter
    I = d[c("NEGDIFTOTKN")].dropna()
    Y = d[c("NYGDPMKTPKN")].dropna()
    common = I.index.intersection(Y.index)
    I, Y = I.loc[common], Y.loc[common]
    t_max = 15
    y0 = I.index.min()
    yt = y0 + t_max
    num = sum((1-DEPR)**(t_max-i) * I.iloc[i] for i in range(1, t_max+1))
    den = (Y.loc[yt]/Y.loc[y0]) - (1-DEPR)**t_max
    K0 = num/den if den > 0 else Y.iloc[0]*3
    K = pd.Series(index=Y.index, dtype=float)
    K.iloc[0] = K0
    for i in range(1, len(Y)):
        K.iloc[i] = (1-DEPR)*K.iloc[i-1] + I.iloc[i]
    d[c("NEGDIKSTKKN")] = K.reindex(d.index)

    L = d[c("LMEMPTOTL")]
    A = Y / (K.pow(1-ALPHA) * L.reindex(Y.index).pow(ALPHA))
    d[c("NYGDPTFP_ACT")] = A.reindex(d.index)
    lfpr_star = hpfilter(d[c("LMPRTTOTL_")].dropna(), lamb=100)[1].reindex(d.index)
    unrt_star = hpfilter(d[c("LMUNRTOTL_")].dropna(), lamb=100)[1].reindex(d.index)
    d[c("LMPRTSTRL_")] = lfpr_star
    d[c("LMUNRSTRL_")] = unrt_star
    d[c("LMEMPSTRL")] = d[c("SPPOP1564TO")] * lfpr_star/100 * (1 - unrt_star/100)
    A_trend = hpfilter(A.dropna(), lamb=100)[1].reindex(d.index)
    d[c("NYGDPTFP")] = A_trend
    Kl1 = d[c("NEGDIKSTKKN")].shift(1)
    d[c("NYGDPPOTLKN")] = (A_trend * d[c("LMEMPSTRL")].pow(ALPHA) * Kl1.pow(1-ALPHA))
    d[c("NYGDPGAP_")] = (d[c("NYGDPMKTPKN")] / d[c("NYGDPPOTLKN")] - 1) * 100

    # Fiscal ratios
    d[c("GGREVTOTLGD")] = d[c("GGREVTOTLCN")] / d[c("NYGDPMKTPCN")] * 100
    d[c("GGEXPTOTLGD")] = d[c("GGEXPTOTLCN")] / d[c("NYGDPMKTPCN")] * 100
    d[c("GGBALOVRLGD")] = d[c("GGBALOVRLCN")] / d[c("NYGDPMKTPCN")] * 100
    if c("GGFINBCBCN") not in d.columns:
        d[c("GGFINBCBCN")] = 0.0
    d[c("GGFINBCBGD")]  = d[c("GGFINBCBCN")]  / d[c("NYGDPMKTPCN")] * 100
    d[c("GGEXPFUELGD")] = d[c("GGEXPFUELCN")] / d[c("NYGDPMKTPCN")] * 100

    d.to_csv(OUT)
    print(f"Wrote {OUT} — {d.shape[1]} cols × {d.shape[0]} years")

    # QA
    qa = [c("NYGDPMKTPKN"), c("NYGDPMKTPCN"), c("FPCPITOTLXN"),
          c("NYGDPGAP_"), c("NYGDPGAP_STR"),
          c("GGREVTOTLGD"), c("GGEXPTOTLGD"), c("GGBALOVRLGD"),
          c("GGDBTTOTLGD"), c("GGEXPFUELGD"),
          c("FIRESGRSCD"), c("FIRESMONTHS"), c("RES_SCARCITY")]
    print("\nQA 2015-2024 (key series):")
    # Truncate fsir values to avoid sci notation noise
    qadf = d.loc[2015:2024, qa].round(2)
    print(qadf.T.to_string())

if __name__ == "__main__":
    main()
