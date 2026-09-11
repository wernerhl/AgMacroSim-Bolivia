# 00 v1 registry: assets, template, growth-input registry

## Assets confirmed present and readable
| Asset | Location | Status for v1 |
|---|---|---|
| Completed DSA (16 files) | `MFMOD_BOL/DSA/outputs/`, `MFMOD_BOL/DSA/exhibits/` | Present, reproduces from `run_all.sh`. Reused as the quantitative backbone; core in `02_dsa_core.md` reused unchanged. |
| MEFP (uploaded) | `MEFP_MEMORANDO DE POLITICAS ECONOMICAS Y FINANCIERAS.pdf` | Present, 19 pages. Page-cited in the DSA `01_baseline.md`. |
| MFMod-BOL v5 (Augmented MFMOD-Bolivia, AI Analytics) | `MFMOD_BOL/` | Present. Independent 2025 growth call minus 3.3 percent; used for the growth cross-check. |
| 754-entity SOE file | `analysis/entidades_publicas_bolivia.csv` | Present as an entity directory (names, sectors, active years). It carries no income statements, so it sizes the SOE universe (741 non-financial public entities) but not their losses. Contingent-liability magnitude is a documented range; see `02_new_scenarios.md`. |
| Fiscal database (README stack) | `analysis/`, `sources/` | Present; used for the contingent-liability components and the historical series. |
| ISAE ("Smog, Not Lights", NO2 nowcast) | pipeline and reproduction package | **Not in this environment.** The published reads are used as supplied (Section 1 and Appendix B of the work order); the reproduction package is recorded as a v2 input. |
| Situational analysis and pre-drafted risk structure | referenced | **Not found as a discrete file in this environment.** The eight-risk taxonomy is built for v1 from the DSA findings, the MEFP's own risk section (p.4, para 9), and the growth cross-check; the related political-economy evidence is in `Who_Owns_the_Rents_and_the_Reform.md` and is cited. Recorded as a v2 reconciliation input if a prior draft exists. |
| MFMod-microsim engine and EH survey | referenced | **Not accessible for an end-to-end run in this environment.** The distributional overlay states direction and defers magnitude; see `03_overlay.md`. |
| Fuel-incidence work order | referenced | Used as the delegated source for the fuel-price incidence magnitude. |

## Template
AI Analytics LaTeX report, `article` class, house format per Appendix A: TikZ risk matrix, booktabs
tables, restrained institutional palette (petrol-slate structural colour, single accent for the top
risk band), serif headings with sans body, masthead and signature block, footer
"AI Analytics, contact@aianalytics.tech". Built in `AIAnalytics_Bolivia_IMF_ProgramRisk_v1.tex`.

## Growth-input registry (three independent near-term reads)
| Source | 2025 | 2026 window | Bracket | Property |
|---|---|---|---|---|
| MEFP (program) | minus 1.6 (cited, p.2) | about minus 1.0 (program-consistent) | n.a. | official, the program's own path |
| MFMod-BOL v5 | minus 3.3 | model path | n.a. | independent structural model, pre-program vintage |
| ISAE (NO2 nowcast) | window read | minus 2.8 | headline CI [minus 4.9, minus 0.6]; paper combined [minus 5.2, minus 0.4]; fire-adjusted minus 1.4; decree lower toward minus 6 | independent nowcast, five-to-six-month lead over IGAE (correlation 0.79 to 0.93 at that lead), IGAE-validated, deflator-free |

### ISAE scope, recorded explicitly
The ISAE disciplines the near term only, to its nowcast horizon (the window September 2025 to August
2026). It is a real-GDP proxy through combustion (the sectors that are about 40 percent of GDP) and
carries its own bracket. It has no signal for the 2028-and-after recovery; that horizon stays
MEFP-based in every exhibit and is flagged as such. The growth read is the counterfactual-gap method
(the NO2 gap divided by the contraction-regime elasticity), not levels translated through a beta.
