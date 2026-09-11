"""
Step 6: Interface — polish the output, compute historical ratios consistently,
write the final deliverable and a narrative markdown summary.
"""
import os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOLN = os.path.join(ROOT, "Output", "BOLSoln.csv")
SUM  = os.path.join(ROOT, "Output", "BOL_projection_summary.csv")
FINAL = os.path.join(ROOT, "Output", "BOL_MFMod_projections_2020_2027.csv")
NOTE = os.path.join(ROOT, "Output", "BOL_MFMod_summary.md")

CTY = "BOL"
def c(x): return f"{CTY}{x}"

def main():
    d = pd.read_csv(SOLN, index_col="year")
    d.index = d.index.astype(int)

    # Backfill historical fiscal ratios
    for y in d.index:
        if pd.notna(d.loc[y, c("NYGDPMKTPCN")]) and pd.notna(d.loc[y, c("GGBALOVRLCN")]):
            d.loc[y, c("GGBALOVRLGD")] = (d.loc[y, c("GGBALOVRLCN")] /
                                          d.loc[y, c("NYGDPMKTPCN")] * 100)
        if pd.notna(d.loc[y, c("NYGDPMKTPCN")]) and pd.notna(d.loc[y, c("GGDBTTOTLCN")]):
            d.loc[y, c("GGDBTTOTLGD")] = (d.loc[y, c("GGDBTTOTLCN")] /
                                          d.loc[y, c("NYGDPMKTPCN")] * 100)

    rows = []
    for y in range(2018, 2028):
        if y not in d.index: continue
        yp = y - 1
        def g(col):
            a = d.loc[y, col]; b = d.loc[yp, col] if yp in d.index else None
            if pd.isna(a) or pd.isna(b) or b == 0: return np.nan
            return 100 * (a / b - 1)
        row = {
            "year": y,
            "GDP_real_bnBs15":  d.loc[y, c("NYGDPMKTPKN")] / 1e9,
            "GDP_growth_pct":   g(c("NYGDPMKTPKN")),
            "GDP_nom_bnBs":     d.loc[y, c("NYGDPMKTPCN")] / 1e9,
            "GDP_nom_bnUSD":    d.loc[y, c("NYGDPMKTPCN")] / d.loc[y, c("PANUSATLS")] / 1e9,
            "CPI_inflation":    g(c("FPCPITOTLXN")),
            "Output_gap_pct":   d.loc[y, c("NYGDPGAP_")],
            "Fiscal_bal_pctGDP": d.loc[y, c("GGBALOVRLGD")],
            "Debt_pctGDP":      d.loc[y, c("GGDBTTOTLGD")],
            "CA_bnUSD":         d.loc[y, c("BNCABFUNDCD")] / 1e9,
            "Employment_mn":    d.loc[y, c("LMEMPTOTL")] / 1e6,
            "UNR_pct":          d.loc[y, c("LMUNRTOTL_")],
            "ConsPriv_g_pct":   g(c("NECONPRVTKN")),
            "InvPriv_g_pct":    g(c("NEGDIFPRVKN")),
            "Exports_g_pct":    g(c("NEEXPGNFSKN")),
            "Imports_g_pct":    g(c("NEIMPGNFSKN")),
            "Agr_g_pct":        g(c("NVAGRTOTLKN")),
            "Ind_g_pct":        g(c("NVINDTOTLKN")),
            "Srv_g_pct":        g(c("NVSRVTOTLKN")),
        }
        rows.append(row)
    summ = pd.DataFrame(rows).set_index("year")
    summ.round(2).to_csv(FINAL)
    print("Final summary saved to:", FINAL)
    print()
    print(summ.T.round(2).to_string())

    # Narrative note
    note = [
        "# MFMod-BOL — Baseline Projections 2026-2027",
        "",
        "Implementation of the World Bank Macro-Fiscal Model (Burns et al. 2019, WPS 8965)",
        "for Bolivia. Data drawn from WDI + local BolBudget fiscal database (2017-2024).",
        "",
        "## Methodology",
        "- **Supply side**: Cobb-Douglas production (α=0.55), trend TFP via HP filter (λ=100),",
        "  capital stock via perpetual inventory (δ=0.05). Potential GDP rolled forward.",
        "- **Demand side**: ECM equations for C, I_priv, X, M estimated on 1995-2024 annual data.",
        "- **Prices**: Phillips-curve CPI (gap semi-elasticity 0.15, 50/50 backward-/forward-looking).",
        "- **Fiscal**: Revenue/expenditure held at 2024 effective ratios (30.6% and 39.3% of GDP);",
        "  debt evolves endogenously (D_t = D_{t-1} − BB_t). FX held at 6.91 Bs/USD peg.",
        "- **External**: Exports include −3% structural gas-sector decline. World demand proxy grows 5% USD.",
        "- **Solver**: Gauss-Seidel within-year iteration, tolerance 1e-5.",
        "",
        "## Baseline projections",
        "",
        summ.round(2).to_markdown(),
        "",
        "## Key takeaways for 2026-2027",
        "",
        f"- **Growth**: {summ.loc[2026,'GDP_growth_pct']:.1f}% (2026), {summ.loc[2027,'GDP_growth_pct']:.1f}% (2027) —",
        "  subdued, below potential. Reflects productivity drag (TFP −1.6% CAGR since 2014),",
        "  gas-sector decline, and investment weakness after 2024 contraction.",
        f"- **Inflation**: ~2.5% — the Phillips curve prints near target because of the negative",
        f"  output gap (2027: {summ.loc[2027,'Output_gap_pct']:.1f}%) offsetting pass-through.",
        f"- **Fiscal**: Balance held at −8.7% of GDP under BAU. Debt rises to",
        f"  **{summ.loc[2027,'Debt_pctGDP']:.0f}% of GDP** by 2027 — unsustainable without consolidation.",
        f"- **External**: Current account widens modestly as imports recover faster than exports.",
        "",
        "## Caveats",
        "- FX assumed to hold the peg. A parallel-market devaluation would reshape prices, debt",
        "  valuation (55% external), and competitiveness immediately.",
        "- Exports proxy uses BOL nominal USD GDP × 1.5 as world demand — trading-partner import",
        "  demand matrix not included. Refinement: bring in COMTRADE-weighted XMKT.",
        "- Estimation sample (1995-2024) mixes hyperinflation recovery, commodity boom and bust.",
        "  Some ECMs have low R² (Agriculture 0.15, Exports 0.16). Paper default θ=0.2 used where",
        "  estimation was unreliable (CPI, wages).",
        "- Fiscal ECM estimated on only 7 observations (2017-2023 from local database) — treat as",
        "  BAU rule rather than structural reaction function.",
        "- Model uses aggregated GFS revenue/expenditure; not the DPF-expanded hydrocarbon block.",
        "",
        "## Files",
        "",
        "- [`Build/01_fetch_data.py`](../Build/01_fetch_data.py) — WDI fetch, 50/51 WB indicators.",
        "- [`Build/02_create_data.py`](../Build/02_create_data.py) — identities, K stock, potential, gap.",
        "- [`Build/03_equations.py`](../Build/03_equations.py) — ECM estimation (14 equations).",
        "- [`Build/04_extend_exog.py`](../Build/04_extend_exog.py) — 2025-27 exogenous inputs.",
        "- [`Build/05_solve_model.py`](../Build/05_solve_model.py) — Gauss-Seidel simulation.",
        "- [`Build/06_interface.py`](../Build/06_interface.py) — this summary.",
        "- [`Rawdata/bol_data.csv`](../Rawdata/bol_data.csv) — historical panel (93 series).",
        "- [`Rawdata/bol_coefficients.json`](../Rawdata/bol_coefficients.json) — estimated ECM coefficients.",
        "- [`Output/BOLSoln.csv`](BOLSoln.csv) — full solution workfile 1990-2027.",
        "- [`Output/BOL_MFMod_projections_2020_2027.csv`](BOL_MFMod_projections_2020_2027.csv) — summary table.",
    ]
    with open(NOTE, "w") as f:
        f.write("\n".join(note))
    print(f"\nNote saved to {NOTE}")

if __name__ == "__main__":
    main()
