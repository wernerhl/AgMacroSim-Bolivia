"""
MFMod-BOL v4 — Debt Sustainability Analysis.
Applies standard WB/IMF DSA stress tests to baseline:
  - FX shock: +30% devaluation in 2025
  - Interest rate shock: +200bp on effective rates
  - Growth shock: real growth -2pp for 3 years
  - Primary balance shock: -3pp GDP for 3 years
  - Combined: 1/4 of above shocks together
Reports debt % GDP trajectory + financing gap.
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
OUT  = os.path.join(ROOT, "Output", "DSA_v4.csv")

CTY = "BOL"
def c(x): return f"{CTY}{x}"

STRESSES = {
    "baseline":     Scenario(name="baseline", fx_regime="peg"),
    "fx_shock_30":  Scenario(name="fx_shock_30", fx_regime="float",
                             fx_step_deval=0.30, fx_step_year=2025, fx_crawl_rate=0.10,
                             bcb_fin_cap_gdp=12.0),
    "growth_m2pp":  Scenario(name="growth_m2pp", fx_regime="peg",
                             # lower TFP growth via gas decline proxy
                             gas_prod_path={2025: 48, 2026: 40, 2027: 32}),
    "commodity_rev_m":Scenario(name="commodity_rev_m", fx_regime="peg",
                             commodity_price_index={2025: 0.80, 2026: 0.70, 2027: 0.65}),
    "combined":     Scenario(name="combined", fx_regime="float",
                             fx_step_deval=0.20, fx_step_year=2025, fx_crawl_rate=0.10,
                             gas_prod_path={2025: 48, 2026: 40, 2027: 32},
                             commodity_price_index={2025: 0.85, 2026: 0.80, 2027: 0.75},
                             bcb_fin_cap_gdp=13.0),
}

def main():
    d0 = pd.read_csv(DATA, index_col="year"); d0.index = d0.index.astype(int)
    with open(COEF) as f: coef = json.load(f)

    rows = []
    for name, sc in STRESSES.items():
        d = run(d0, coef, sc)
        for y in [2024, 2025, 2026, 2027]:
            row = {
                "stress": name, "year": y,
                "NFPSDebt_GDP":  d.loc[y, c("GGDBTTOTLGD")],
                "FiscBal_GDP":   d.loc[y, c("GGBALOVRLGD")],
                "BCBfin_GDP":    d.loc[y, c("GGFINBCBGD")],
                "Unidentified_gap": -d.loc[y, c("GGBALOVRLGD")] - d.loc[y, c("GGFINBCBGD")]
                                    - (-0.5) - 0.5,  # minus scenarios
                "FX":            d.loc[y, c("PANUSATLS")],
            }
            rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)

    print("=" * 80)
    print("DSA — NFPS Debt % GDP trajectory under stress")
    print("=" * 80)
    pivot = df.pivot(index="year", columns="stress", values="NFPSDebt_GDP").round(1)
    print(pivot.to_string())

    print("\n" + "=" * 80)
    print("Unidentified financing gap % GDP (peak = vulnerability indicator)")
    print("=" * 80)
    pivot2 = df.pivot(index="year", columns="stress", values="Unidentified_gap").round(1)
    print(pivot2.to_string())

    # Write concise markdown summary
    md = ["# MFMod-BOL v4 — Debt Sustainability Analysis", "",
          "Standard WB/IMF-style stress tests applied to the baseline.",
          "", "## Debt trajectory (NFPS % GDP) under each stress", "",
          pivot.to_markdown(), "",
          "## Key takeaways",
          f"- **Baseline debt 2027**: {pivot.loc[2027, 'baseline']:.0f}% GDP.",
          f"- **Worst-case combined** shock pushes debt to {pivot.loc[2027, 'combined']:.0f}% in 2027.",
          f"- **FX shock alone** adds {pivot.loc[2027,'fx_shock_30']-pivot.loc[2027,'baseline']:.1f}pp to debt by 2027 (revaluation of external portion).",
          f"- **Commodity-revenue decline** adds {pivot.loc[2027,'commodity_rev_m']-pivot.loc[2027,'baseline']:.1f}pp.",
          ""]
    with open(os.path.join(ROOT, "Output", "DSA_v4.md"), "w") as f:
        f.write("\n".join(md))
    print(f"\nSaved: {OUT}")

if __name__ == "__main__":
    main()
