# 00 Registry: assets, calibration inputs, caveats

## Models
- **MFMod-BOL** (`MFMOD_BOL/`, v5, April 2026). World Bank MFMod adapted for Bolivia
  (`MFMOD_BOL/MODEL.md`): a structural econometric system of about 50 to 80 equations in seven blocks
  (supply-side Cobb-Douglas potential output; ECM GDP demand; Phillips-curve prices; labor; fiscal
  with endogenous debt; balance of payments; monetary UIP under the peg). Bolivia deviations: a
  regime-switch Phillips curve estimated on a 7-country LATAM panel (a scarcity indicator when
  reserves fall below three months of imports adds about 5.4 points to inflation), an exogenous
  hydrocarbon sub-block, an explicit fuel-subsidy line, and an NFPS debt perimeter. Fiscal and debt
  block present; exchange-rate and price blocks present. Calibration vintage: data through 2024, ECM
  sample 2000 to 2023, coefficients in `MFMOD_BOL/Rawdata/bol_coefficients_v5.json`.
  Runnable form: the v5 pipeline (`Build/41_data_v5.py`, `42_estimate_v5.py`, `43_solve_v5.py`)
  produced `Output/BOLSoln_v5.csv` and a validation against the April-2025 Article IV
  (`Output/BOL_MFMod_v5_vs_IMF.csv`). It was built before this MEFP and benchmarked to the prior
  Article IV, so for this DSA it is used for structure, elasticities, and the reproduction check, not
  as the baseline generator. The debt path is produced by the reduced-form core (Section 3 of the
  work order), as permitted. See `01_repro_check.md`.
- **MFMod-microsim** (macro-to-micro). Not run end to end in this pass. The distributional overlay in
  `04_results.md` states the transmission direction and defers the fuel channel to the companion
  fuel-incidence work order, per the work order instruction. This is recorded as a pending item, not
  a result.

## Data (the README fiscal stack, with vintages)
- SPNF trajectory 1990-2024: `analysis/spnf_long_1990_2024.csv` (35 rows; global and primary balance,
  external and internal interest, wages, capital spending).
- Debt and GDP: `analysis/macro_gdp_debt_2000_2024.csv` (consolidated debt percent GDP, IMF WEO
  vintage; external debt USD; nominal GDP). End-2024 external debt USD 13,420 million; at the peg that
  is about 24.6 percent of GDP, so the FX share of an 80-percent stock is about 0.31, consistent with
  the MEFP statement of more than a third external (p.8, para 21).
- GDP rebase splice: `analysis/gdp_spliced_2000_2024.csv` (the 2016/17 rebase lifts the 2016 level
  from 234.5 to 288.9 billion Bs; the spliced series removes the break).
- INE CPI 1990-2024: `analysis/cpi_index_1990_2024.csv` (end-of-period).
- Fuel subsidy 5-component 2010-2025: `analysis/subsidio_hidrocarburos_comprehensive_Medinaceli2024.csv`.
- Bonos, SOE file (754 entities), tax-by-type 1987-2024, intergovernmental transfers 2001-2022:
  present in `analysis/` and `sources/` per the README stack; used for the contingent-liability and
  revenue-composition reasoning, not as DSA anchors.

## The MEFP (uploaded)
`MEFP_MEMORANDO DE POLITICAS ECONOMICAS Y FINANCIERAS.pdf`, 19 pages. Program: Servicio Ampliado del
Fondo (Extended Fund Facility), 36 months (p.1, intro). Quantitative performance criteria and
indicative targets in Cuadro 1 (p.17); prior actions and structural benchmarks in Cuadro 2 (p.18-19).
Page-cited anchors are transcribed in `01_baseline.md`.

## Two adjustments applied throughout
- **Parallel-rate adjustment.** Official peg 6.96 Bs/USD; transition reference rate about 9.8 that
  reconciles the MEFP's 90-percent market-valuation figure at end-2025; street parallel about 13.5
  (central of the stated 1.7 to 2.2 times overstatement of USD-GDP at the peg). Every debt and GFN
  ratio is reported at the official and the market valuation; the full-parallel valuation is carried
  as the adverse bound. Reconciliation check: the MEFP's own statement that SPNF debt exceeded 80
  percent at the official rate and about 90 percent at the market rate (p.8, para 21) is reproduced by
  an FX share of 0.31 and a reference rate of about 9.8.
- **GDP rebase splice.** The spliced series is used for historical ratios and the growth-rate joint
  distribution; robustness with the unspliced series is reported in `06_robustness.md`.

Data are annual. This is an annual DSA; no high-frequency claims.

## Caveats
- The debt path is reduced-form (identity-based), not a full MFMod-BOL solve. Growth and inflation
  inputs are MEFP-anchored where cited, program-consistent otherwise.
- The 2016/17 rebase and the peg-versus-parallel gap are the two largest sources of level uncertainty;
  both are handled by dual reporting.
- The microsimulation overlay is pending.
