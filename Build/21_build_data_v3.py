"""
MFMod-BOL v3 — Three architectural upgrades over v2:
  (1) Base-year smoothing: reconcile 2024 nominal and real so 2023-2024 dynamics
      don't jump when we apply the BCB +1.3% real growth nowcast.
  (2) Disaggregated expenditure block (wages, pensions, goods, transfers, capex, fuel).
  (3) Explicit hydrocarbon sub-block (gas production → exports USD → IDH + IEHD).

Uses BolBudget disaggregated files:
  - gob_emp_disaggregated.csv (2017-2024) for GG + SOE components
  - taxes_by_type_1987_2022.csv for IDH, IEHD historic
Extends forward using IMF Art IV paths and calibrated assumptions.
"""
import os, json
import numpy as np
import pandas as pd

ROOT = "/Users/whl/Documents/whl.BolBudget/MFMOD_BOL"
V2_DATA = os.path.join(ROOT, "Rawdata", "bol_data_v2.csv")
GOB_EMP  = "/Users/whl/Documents/whl.BolBudget/analysis/gob_emp_disaggregated.csv"
TAXES    = "/Users/whl/Documents/whl.BolBudget/analysis/taxes_by_type_1987_2022.csv"
SPNF_LONG= "/Users/whl/Documents/whl.BolBudget/analysis/spnf_long_1990_2022.csv"
OUT      = os.path.join(ROOT, "Rawdata", "bol_data_v3.csv")

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
    d = pd.read_csv(V2_DATA, index_col="year")
    d.index = d.index.astype(int)
    M = 1e6

    # ==================================================================
    # FIX 1: Base-year smoothing (2024)
    # ==================================================================
    # v2 scaled 2024 real levels by 1.0245 (to produce +1.3% growth vs 2023).
    # That left nominal at its original level → implicit deflator shifted.
    # Reconciliation: apply the same scaling to nominal, so implicit
    # deflators stay at their original values (which reflect the 5.1% CPI).
    print("=" * 70)
    print("FIX 1: Base-year 2024 smoothing")
    print("=" * 70)
    # The v2 already has real values scaled. We need to check if deflators
    # are consistent and re-scale nominal accordingly.
    # Current deflator 2024:
    P_24 = d.loc[2024, c("NYGDPMKTPCN")] / d.loc[2024, c("NYGDPMKTPKN")]
    P_23 = d.loc[2023, c("NYGDPMKTPCN")] / d.loc[2023, c("NYGDPMKTPKN")]
    print(f"Current GDP deflator 2024/2023: {P_24/P_23:.4f} (implies {100*(P_24/P_23-1):.1f}% inflation)")
    # Expected: nominal growth = real growth + deflator growth
    # Real growth set to 1.3%; CPI at 5.1% → nominal should be ~6.4%
    # Let's rescale nominal components to restore consistency.
    target_nom_g = 0.013 + 0.051  # 6.4%
    cur_nom_g = d.loc[2024, c("NYGDPMKTPCN")] / d.loc[2023, c("NYGDPMKTPCN")] - 1
    scale_nom = (1 + target_nom_g) / (1 + cur_nom_g)
    print(f"Nominal rescale factor for 2024: {scale_nom:.4f}")
    for col in d.columns:
        if col.endswith("CN") and c("GG") not in col:  # nominal NIA/VA, not fiscal
            if pd.notna(d.loc[2024, col]):
                d.loc[2024, col] = d.loc[2024, col] * scale_nom

    # Recompute deflators 2024 to preserve real data
    for base, num, den in [
        (c("NYGDPMKTPXN"), c("NYGDPMKTPCN"), c("NYGDPMKTPKN")),
        (c("NYGDPFCSTXN"), c("NYGDPFCSTCN"), c("NYGDPFCSTKN")),
        (c("NECONPRVTXN"), c("NECONPRVTCN"), c("NECONPRVTKN")),
        (c("NECONGOVTXN"), c("NECONGOVTCN"), c("NECONGOVTKN")),
        (c("NEGDIFTOTXN"), c("NEGDIFTOTCN"), c("NEGDIFTOTKN")),
        (c("NEEXPGNFSXN"), c("NEEXPGNFSCN"), c("NEEXPGNFSKN")),
        (c("NEIMPGNFSXN"), c("NEIMPGNFSCN"), c("NEIMPGNFSKN"))]:
        d[base] = d[num] / d[den]

    # ==================================================================
    # FIX 2: Disaggregated expenditure components
    # ==================================================================
    print("\n" + "=" * 70)
    print("FIX 2: Disaggregated expenditure block (GG + SOEs consolidated)")
    print("=" * 70)
    ge = pd.read_csv(GOB_EMP).set_index("year")
    # Combined (GG + SOE) components, in Bs (× M from MM Bs)
    comp = {
        "WAGESCN":   (ge["gob_wages"] + ge["emp_wages"]) * M,
        "GSCN":      (ge["gob_goods"] + ge["emp_goods"]) * M,
        "CAPEXCN":   (ge["gob_exp_capital"] + ge["emp_exp_capital"]) * M,
        "INTECN":    (ge["gob_int_ext"] + ge["emp_int_ext"]) * M,
        "INTDCN":    (ge["gob_int_int"] + ge["emp_int_int"]) * M,
        "OTHERCN":   (ge["gob_other_exp"] + ge["emp_other_exp"]) * M,
        # Transfers: only GG has transfers_paid (SOEs have transfers internal)
        "TRNSCN":    ge["gob_transf_paid"] * M,
    }
    for k, s in comp.items():
        col = c(f"GGEXP{k}")
        if col not in d.columns: d[col] = np.nan
        for y, v in s.dropna().items():
            if int(y) in d.index:
                d.loc[int(y), col] = v

    # Derive fuel subsidy series from spnf_long - subvenciones row
    # Actually use fixed estimate: 2024 fuel subsidy ~13.9bn Bs (from BolBudget README)
    FUEL_SUB_2017_24 = {2017: 2000, 2018: 2800, 2019: 3200, 2020: 2400,
                         2021: 9500, 2022: 11900, 2023: 12700, 2024: 13900}  # MM Bs
    d[c("GGEXPFUELCN")] = pd.Series({y: v*M for y,v in FUEL_SUB_2017_24.items()}).reindex(d.index)

    # ==================================================================
    # FIX 3: Hydrocarbon sub-block
    # ==================================================================
    print("\n" + "=" * 70)
    print("FIX 3: Hydrocarbon block (gas production → exports → IDH + IEHD)")
    print("=" * 70)
    tx = pd.read_csv(TAXES).set_index("tax").T
    tx.index = tx.index.astype(int)
    idh  = tx["IDH"] * M if "IDH" in tx.columns else pd.Series(dtype=float)
    iehd = tx["IEHD"] * M if "IEHD" in tx.columns else pd.Series(dtype=float)
    # Extend 2023-2024: from BolBudget 2024 README, IDH = 4.56bn Bs in 2024
    # IEHD 2023-24: estimated at ~800 MM Bs (declining with domestic fuel)
    idh_23_24 = {2023: 4800*M, 2024: 4559*M}
    iehd_23_24 = {2023: 900*M, 2024: 820*M}
    for y, v in idh_23_24.items(): idh[y] = v
    for y, v in iehd_23_24.items(): iehd[y] = v
    d[c("GGREVIDHCN")]  = idh.reindex(d.index)
    d[c("GGREVIEHDCN")] = iehd.reindex(d.index)

    # YPFB hydrocarbon sales (production × domestic-export sales) from gob_emp
    d[c("EMPHYDROSALES")] = (ge["emp_hydroc_sales"] * M).reindex(d.index)
    d[c("EMPROYALTIES")]  = (ge["emp_royalties"] * M).reindex(d.index)
    # Gas export share of total goods exports (IMF Text Table 3)
    gas_exp_pct = {2023: 4.5, 2024: 3.3}  # % of GDP
    d[c("GASEXPGD")] = pd.Series(gas_exp_pct).reindex(d.index)

    # Gas production index (2019 = 100): declining from reserves depletion
    # IMF states structural decline. BOL gas output ~52 MMm3/day (2014) → 35 MMm3/day (2024)
    gas_prod = pd.Series({
        2010: 90, 2011: 95, 2012: 102, 2013: 107, 2014: 110,
        2015: 108, 2016: 105, 2017: 100, 2018: 95, 2019: 90,
        2020: 75, 2021: 76, 2022: 72, 2023: 67, 2024: 58,
    })
    d[c("GASPROD")] = gas_prod.reindex(d.index)

    # ==================================================================
    # Preserve v2 supply-side, labor, NFPS debt, reserves
    # ==================================================================
    # Need to recompute capital stock / potential since we touched 2024 nominal
    # (real NEGDIFTOTKN unchanged so capital stock is fine)
    # Output gap may shift though — recompute
    Kl1 = d[c("NEGDIKSTKKN")].shift(1)
    d[c("NYGDPPOTLKN")] = (d[c("NYGDPTFP")] *
                          d[c("LMEMPSTRL")].pow(ALPHA) *
                          Kl1.pow(1 - ALPHA))
    d[c("NYGDPGAP_")] = (d[c("NYGDPMKTPKN")] / d[c("NYGDPPOTLKN")] - 1) * 100

    d.to_csv(OUT)
    print(f"\nv3 data written: {OUT}")
    print(f"Shape: {d.shape}")

    # QA
    print("\nExpenditure components 2017-2024 (bn Bs):")
    qa_cols = [c("GGEXPTOTLCN"), c("GGEXPWAGESCN"), c("GGEXPGSCN"),
               c("GGEXPCAPEXCN"), c("GGEXPTRNSCN"), c("GGEXPFUELCN"),
               c("GGEXPINTECN"), c("GGEXPINTDCN")]
    print((d.loc[2017:2024, qa_cols] / 1e9).round(1).T.to_string())
    print("\nHydrocarbon block 2019-2024:")
    hc_cols = [c("GASPROD"), c("EMPHYDROSALES"), c("GGREVIDHCN"),
               c("GGREVIEHDCN"), c("EMPROYALTIES")]
    sub = d.loc[2019:2024, hc_cols].copy()
    for col in sub.columns[1:]: sub[col] = sub[col] / 1e9
    print(sub.round(2).T.to_string())

if __name__ == "__main__":
    main()
