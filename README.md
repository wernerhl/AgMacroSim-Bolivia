# AgMacroSim-Bolivia

**Augmented MFMOD-Bolivia** — a macro-structural model of Bolivia, with a debt-sustainability
analysis (DSA) and an IMF Extended Fund Facility program-risk assessment built on top of it.

Built by **AI Analytics** (https://aianalytics.tech). Contact: contact@aianalytics.tech.

## What this is
An adaptation of the World Bank Macro-Fiscal Model (MFMod; Burns, Campagne, Jooste, Stephan, Bui
2019) to Bolivia: a structural econometric system of ~50–80 equations in seven blocks (supply,
GDP demand, prices, labour, fiscal with endogenous debt, balance of payments, monetary), annual
cadence, Gauss–Seidel simultaneous solver. Bolivia-specific features include a regime-switch
Phillips curve estimated on a LATAM panel, an exogenous hydrocarbon sub-block, an explicit
fuel-subsidy line, and an NFPS debt perimeter. See `MODEL.md` for the full specification and
calibration vintage (v5).

## Layout
```
Build/      model pipeline (data build, estimation, solve; versions 01–43)
Output/     solutions, projections, IMF comparisons, validation
Rawdata/    calibrated coefficients and inputs
MODEL.md    model documentation
DSA/        debt-sustainability analysis (reduced-form core + scenarios, seeded, reproducible)
  outputs/  DSA notes, findings memo, identification note, DSA table
  exhibits/ tables and figures
  code/     dsa_core.py, dsa_analysis.py, dsa_exhibits.py
  run_all.sh
DSA/v1/     AI Analytics program-risk report (v1): new scenarios, growth cross-check, signed PDF
```

## Reproduce
- Model: run the `Build/` pipeline (see `MODEL.md`).
- DSA: `cd DSA && ./run_all.sh` (master seed 20260910).
- Program-risk v1: `cd DSA/v1 && python3 code/v1_scenarios.py && python3 code/v1_figures.py`,
  then compile `outputs/AIAnalytics_Bolivia_IMF_ProgramRisk_v1.tex`.

## Notes
Debt figures are reported at both the official peg and the market/parallel valuation. Baseline
anchors are from the IMF program memorandum (page-cited in `DSA/outputs/01_baseline.md`); the debt
core is reduced-form. See `DSA/outputs/IDENTIFICATION_NOTE.md` for the provenance of every headline.

*Analytical product; not investment or legal advice.*
