"""
MFMod-BOL v4 — Macro-to-microsim export.
Produces the MFMod-microsim input Excel (matching EXMPL-MFMod-microsim.do schema)
with Bolivia macro projections as tabs per scenario.
Schema per Summer University 2022 template:
  year | MFM_GDP | MFM_WA | MFM_empl | MFM_wage | MFM_cons | MFM_CPI | MFM_sect1 | MFM_sect2 | MFM_sect3
  (Agr | Ind | Services VA in real LCU)
"""
import os, json, sys
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from importlib import import_module
core = import_module("31_core_v4")
scenarios = import_module("32_scenarios_v4")
Scenario = core.Scenario
run = core.run

ROOT = "/Users/whl/Documents/whl.BolBudget/MFMOD_BOL"
DATA = os.path.join(ROOT, "Rawdata", "bol_data_v3.csv")
COEF = os.path.join(ROOT, "Rawdata", "bol_coefficients_v2.json")
OUT  = os.path.join(ROOT, "Output", "BOL-MFMod-input.xlsx")

CTY = "BOL"
def c(x): return f"{CTY}{x}"

def prep_sheet(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for y in range(2010, 2028):
        if y not in d.index: continue
        rows.append({
            "year":     y,
            "MFM_GDP":  d.loc[y, c("NYGDPMKTPKN")],     # real GDP
            "MFM_WA":   d.loc[y, c("SPPOPWORK")] / 1e3,  # thousands
            "MFM_empl": d.loc[y, c("LMEMPTOTL")] / 1e3,  # thousands
            "MFM_wage": d.loc[y, c("NEWRTTOTLXN")],      # LCU per worker
            "MFM_cons": d.loc[y, c("NECONPRVTKN")],
            "MFM_CPI":  d.loc[y, c("FPCPITOTLXN")],
            "MFM_sect1": d.loc[y, c("NVAGRTOTLKN")],
            "MFM_sect2": d.loc[y, c("NVINDTOTLKN")],
            "MFM_sect3": d.loc[y, c("NVSRVTOTLKN")],
        })
    return pd.DataFrame(rows)

def main():
    d0 = pd.read_csv(DATA, index_col="year"); d0.index = d0.index.astype(int)
    with open(COEF) as f: coef = json.load(f)

    # Pick two scenarios to match EXMPL template (BaU, CCdam-equivalent)
    # Use baseline + orderly (consolidation = policy intervention)
    with pd.ExcelWriter(OUT) as writer:
        for name in ["baseline", "orderly", "disorderly", "commodity_boom"]:
            sc = scenarios.SCEN[name]
            d = run(d0, coef, sc)
            sheet = prep_sheet(d)
            # Rename to match template: "BaU" / "CCdam" etc.
            label = {"baseline": "BaU", "orderly": "Consolidation",
                     "disorderly": "Crisis", "commodity_boom": "CommodityBoom"}[name]
            sheet.to_excel(writer, sheet_name=label, index=False)
            print(f"  Wrote sheet '{label}' with {len(sheet)} rows")
    print(f"\nSaved: {OUT}")
    print(f"This file feeds directly into:")
    print(f"  /Users/whl/pCloud Drive/_WB.CCDR/LCA/OECS CCDR/Equity Policy Lab Material/MFMOD/Summer University 2022/EXMPL-MFMod-microsim.do")
    print(f"Set global input_MFMod to point to {OUT}, global scenario_list to \"BaU Consolidation Crisis CommodityBoom\"")

if __name__ == "__main__":
    main()
