"""
Step 1: Fetch Bolivia macro data from World Bank WDI and assemble the MFMod data panel.
Maps directly to the WB codes used in CCDR_ZWE/Build/createdataupdatetemplate.prg.
Output: Rawdata/bol_raw.csv with MFMod-named series.
"""
import os
import pandas as pd
import wbgapi as wb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "Rawdata", "bol_raw.csv")
LOG = os.path.join(ROOT, "logs", "01_fetch_data.log")

CTY = "BOL"
YEARS = range(1990, 2025)

# WB WDI indicator -> MFMod series name (suffix only; prefix BOL added on save)
SERIES = {
    # Memo / population
    "SP.POP.TOTL":                "SPPOPTOTL",
    "SP.POP.1564.TO":             "SPPOP1564TO",
    # Real GDP expenditure (constant LCU)
    "NY.GDP.MKTP.KN":             "NYGDPMKTPKN",
    "NE.CON.PRVT.KN":             "NECONPRVTKN",
    "NE.CON.GOVT.KN":             "NECONGOVTKN",
    "NE.GDI.FTOT.KN":             "NEGDIFTOTKN",
    "NE.GDI.STKB.KN":             "NEGDISTKBKN",
    "NE.EXP.GNFS.KN":             "NEEXPGNFSKN",
    "NE.IMP.GNFS.KN":             "NEIMPGNFSKN",
    "NY.GDP.DISC.KN":             "NYGDPDISCKN",
    # Nominal GDP expenditure (current LCU)
    "NY.GDP.MKTP.CN":             "NYGDPMKTPCN",
    "NE.CON.PRVT.CN":             "NECONPRVTCN",
    "NE.CON.GOVT.CN":             "NECONGOVTCN",
    "NE.GDI.FTOT.CN":             "NEGDIFTOTCN",
    "NE.GDI.STKB.CN":             "NEGDISTKBCN",
    "NE.EXP.GNFS.CN":             "NEEXPGNFSCN",
    "NE.IMP.GNFS.CN":             "NEIMPGNFSCN",
    # Production side (real and nominal)
    "NV.AGR.TOTL.KN":             "NVAGRTOTLKN",
    "NV.IND.TOTL.KN":             "NVINDTOTLKN",
    "NV.SRV.TOTL.KN":             "NVSRVTOTLKN",
    "NV.AGR.TOTL.CN":             "NVAGRTOTLCN",
    "NV.IND.TOTL.CN":             "NVINDTOTLCN",
    "NV.SRV.TOTL.CN":             "NVSRVTOTLCN",
    # Current USD GDP (for BoP scaling and per-capita)
    "NY.GDP.MKTP.CD":             "NYGDPMKTPCD",
    # Balance of payments (current USD)
    "BX.GSR.MRCH.CD":             "BXGSRMRCHCD",
    "BX.GSR.NFSV.CD":             "BXGSRNFSVCD",
    "BM.GSR.MRCH.CD":             "BMGSRMRCHCD",
    "BM.GSR.NFSV.CD":             "BMGSRNFSVCD",
    "BN.CAB.XOKA.CD":             "BNCABFUNDCD",
    # Remittances (current USD)
    "BX.TRF.PWKR.CD.DT":          "BXFSTREMTCD",
    "BM.TRF.PWKR.CD.DT":          "BMFSTREMTCD",
    # FDI net inflows (current USD)
    "BX.KLT.DINV.CD.WD":          "BFCAFFFDICD",
    # Reserves (current USD)
    "FI.RES.TOTL.CD":             "FIRESTOTLCD",
    # Exchange rate (official LCU/USD, period avg)
    "PA.NUS.FCRF":                "PANUSATLS",
    # CPI (2010=100)
    "FP.CPI.TOTL":                "FPCPITOTLXN",
    # Fiscal (WB codes)
    "GC.REV.XGRT.CN":             "GGREVTOTLCN",
    "GC.TAX.TOTL.CN":             "GGREVTAXTCN",
    "GC.XPN.TOTL.CN":             "GGEXPTOTLCN",
    "GC.XPN.INTP.CN":             "GGEXPINTPCN",
    "GC.NLD.TOTL.GD.ZS":          "GGBALOVRLGD",
    "GC.DOD.TOTL.GD.ZS":          "GGDBTTOTLGD",
    # Fiscal as % GDP fallbacks
    "GC.REV.XGRT.GD.ZS":          "GGREVTOTLGD",
    "GC.XPN.TOTL.GD.ZS":          "GGEXPTOTLGD",
    "GC.TAX.TOTL.GD.ZS":          "GGREVTAXTGD",
    # Labor
    "SL.EMP.TOTL":                "LMEMPTOTL",
    "SL.UEM.TOTL.ZS":             "LMUNRTOTL_",
    "SL.TLF.CACT.ZS":             "LMPRTTOTL_",
    # Monetary
    "FR.INR.LEND":                "FMLBLPOLYFR",   # lending rate as proxy for policy rate
    "FM.LBL.BMNY.CN":             "FMLBLMTWOCN",   # broad money M2 (LCU)
    # Oil (hydrocarbon-heavy for Bolivia)
    "NY.GDP.PETR.RT.ZS":          "NVOILTOTLGD",
    "TX.VAL.FUEL.ZS.UN":          "BXGOILSHRPC",
}

def fetch(code: str) -> pd.Series:
    try:
        df = wb.data.DataFrame(code, CTY, time=range(1990, 2025), labels=False,
                               numericTimeKeys=True, skipBlanks=False)
        if df.empty:
            return pd.Series(dtype=float)
        s = df.iloc[0]
        s.index = s.index.astype(int)
        return s.sort_index()
    except Exception as e:
        print(f"  FAIL {code}: {e}")
        return pd.Series(dtype=float)

def main():
    years = list(YEARS)
    out = pd.DataFrame(index=years)
    out.index.name = "year"
    log_lines = [f"# MFMod-BOL data fetch log\n# country={CTY}"]
    n_ok = 0
    for code, name in SERIES.items():
        s = fetch(code)
        col = f"{CTY}{name}"
        if s.empty:
            out[col] = pd.NA
            log_lines.append(f"MISS  {code:<25s} -> {col}")
        else:
            out[col] = s.reindex(years)
            n_ok += 1
            first = s.dropna().index.min() if not s.dropna().empty else "-"
            last  = s.dropna().index.max() if not s.dropna().empty else "-"
            log_lines.append(f"OK    {code:<25s} -> {col:<20s} [{first}-{last}]")
        print(f"  {code:<25s} {'OK' if not s.empty else 'MISS'}")
    out.to_csv(OUT)
    with open(LOG, "w") as f:
        f.write("\n".join(log_lines))
    print(f"\nFetched {n_ok}/{len(SERIES)} series -> {OUT}")

if __name__ == "__main__":
    main()
