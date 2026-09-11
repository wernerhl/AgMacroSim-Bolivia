"""
MFMod-BOL v4 — Scenario library.
Runs 4 canonical scenarios using core_v4 engine:
  1. baseline        (IMF-aligned: peg, no reform, fuel subsidy drift)
  2. orderly         (IMF Annex III: 35% step deval + fiscal consolidation)
  3. disorderly      (reserves run out 2026 → 70% deval, no consolidation)
  4. commodity_boom  (gas prices +30%, lithium tailwind, no reform)
"""
import os, json, sys
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from importlib import import_module
core = import_module("31_core_v4")
Scenario = core.Scenario
run = core.run

ROOT = "/Users/whl/Documents/whl.BolBudget/MFMOD_BOL"
DATA = os.path.join(ROOT, "Rawdata", "bol_data_v3.csv")
COEF = os.path.join(ROOT, "Rawdata", "bol_coefficients_v2.json")
OUT  = os.path.join(ROOT, "Output", "SCEN_v4.csv")

CTY = "BOL"
def c(x): return f"{CTY}{x}"

SCEN = {
    "baseline": Scenario(
        name="baseline", fx_regime="peg",
        fuel_subsidy_path_gdp={2025: 0.040, 2026: 0.042, 2027: 0.044},
    ),
    "orderly": Scenario(  # IMF recommendation (CR 25/116 Annex III)
        name="orderly", fx_regime="float",
        fx_step_deval=0.35, fx_step_year=2025, fx_crawl_rate=0.02,
        fuel_subsidy_path_gdp={2025: 0.020, 2026: 0.010, 2027: 0.000},  # phased out
        wage_freeze=True,
        cap_spending_cut_pp={2025: 0.005, 2026: 0.010, 2027: 0.010},
        tax_ratchet_pp={2025: 0.005, 2026: 0.015, 2027: 0.020},
        monetary_rule="taylor",
        bcb_fin_cap_gdp=3.0,  # tight: near-zero monetary financing
    ),
    "disorderly": Scenario(
        name="disorderly", fx_regime="float",
        fx_step_deval=0.70, fx_step_year=2026, fx_crawl_rate=0.15,
        fuel_subsidy_path_gdp={2025: 0.045, 2026: 0.055, 2027: 0.050},
        bcb_fin_cap_gdp=15.0,
        reserves_path={2025: 1000, 2026: 200, 2027: 200},
    ),
    "commodity_boom": Scenario(
        name="commodity_boom", fx_regime="peg",
        commodity_price_index={2025: 1.10, 2026: 1.25, 2027: 1.30},
        gas_prod_path={2025: 55, 2026: 52, 2027: 50},  # less steep decline
        fuel_subsidy_path_gdp={2025: 0.038, 2026: 0.038, 2027: 0.037},
    ),
}

def main():
    d0 = pd.read_csv(DATA, index_col="year"); d0.index = d0.index.astype(int)
    with open(COEF) as f: coef = json.load(f)

    rows = []
    for name, sc in SCEN.items():
        print(f"\n{'='*60}\nRunning scenario: {name}\n{'='*60}")
        d = run(d0, coef, sc)
        for y in [2024, 2025, 2026, 2027]:
            yp = y - 1
            row = {
                "scenario": name, "year": y,
                "RealGDP_g":    100*(d.loc[y,c("NYGDPMKTPKN")]/d.loc[yp,c("NYGDPMKTPKN")]-1),
                "CPI":          100*(d.loc[y,c("FPCPITOTLXN")]/d.loc[yp,c("FPCPITOTLXN")]-1),
                "FiscBal_GDP":  d.loc[y,c("GGBALOVRLGD")],
                "NFPSDebt_GDP": d.loc[y,c("GGDBTTOTLGD")],
                "FX_LCUperUSD": d.loc[y,c("PANUSATLS")],
                "NomGDP_USDbn": d.loc[y,c("NYGDPMKTPCD")]/1e9,
                "BCBfin_GDP":   d.loc[y,c("GGFINBCBGD")],
                "UNR":          d.loc[y,c("LMUNRTOTL_")],
                "CA_GDP":       d.loc[y,c("BNCABFUNDCD")]/d.loc[y,c("NYGDPMKTPCD")]*100,
            }
            rows.append(row)
        for y_print in [2025, 2026, 2027]:
            print(f"  {y_print}: GDPg={row['RealGDP_g']:+5.1f}% CPI={row['CPI']:+5.1f}% "
                  f"Bal={row['FiscBal_GDP']:+5.1f}% Debt={row['NFPSDebt_GDP']:.0f}% "
                  f"FX={row['FX_LCUperUSD']:.1f}" if row['year'] == y_print else "", end="")

    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)
    print("\n\n" + "=" * 80)
    print("SCENARIO COMPARISON — 2026")
    print("=" * 80)
    pivot = df[df.year == 2026].set_index("scenario")[
        ["RealGDP_g", "CPI", "FiscBal_GDP", "NFPSDebt_GDP", "FX_LCUperUSD", "NomGDP_USDbn"]
    ].round(1)
    print(pivot.to_string())
    print("\nSaved:", OUT)

if __name__ == "__main__":
    main()
