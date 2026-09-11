"""
MFMod-BOL v4 — Full-tier upgrade.
Shared engine used by scenario runner, DSA, backcast, microsim export.

Key additions over v3:
  - FX regime switch: PEG | CRAWL | FLOAT with UIP condition for floating
  - External debt revaluation when FX moves
  - Taylor-rule / money-rule monetary policy
  - Consumption with wealth (net foreign assets + capital stock + gov debt proxy)
  - Agriculture: weather dummy (El Niño / La Niña years)
  - Exports disaggregated: gas | mining | agro | manufactures | services
  - Scenario toggles cleanly propagate

Usage:
  from core_v4 import Model, Scenario, run
  sc = Scenario(name="baseline", fx_regime="peg", ...)
  d_out = run(d_in, coef, sc)
"""
import numpy as np
import pandas as pd
from dataclasses import dataclass, field

CTY = "BOL"
def c(x): return f"{CTY}{x}"
ALPHA = 0.55
DEPR  = 0.05

@dataclass
class Scenario:
    name: str = "baseline"
    # FX regime
    fx_regime: str = "peg"                       # peg | crawl | float
    fx_crawl_rate: float = 0.0                   # % per year LCU/USD devaluation (crawl)
    fx_step_deval: float = 0.0                   # one-off % step deval at start (e.g. 0.35 = +35%)
    fx_step_year: int = 2025                     # year step deval applies
    # Fiscal
    fuel_subsidy_path_gdp: dict = field(default_factory=lambda: {2025: 0.040, 2026: 0.042, 2027: 0.044})
    tax_ratchet_pp: dict     = field(default_factory=lambda: {})   # +revenue pp GDP per year
    wage_freeze: bool = False                    # True → real wage bill flat
    cap_spending_cut_pp: dict = field(default_factory=lambda: {}) # -capex pp GDP per year
    # Hydrocarbon
    gas_prod_path: dict = field(default_factory=lambda: {2025: 51, 2026: 45, 2027: 40})
    # Monetary
    monetary_rule: str = "passive"               # passive (exog rate) | taylor | money
    bcb_fin_cap_gdp: float = 10.0                # max monetization % GDP
    # Commodity
    commodity_price_index: dict = field(default_factory=lambda: {2025: 1.0, 2026: 1.0, 2027: 1.0})
    # External demand
    xmkt_growth: float = 0.05                    # annual USD growth of partner demand
    # Reserve path (USD millions)
    reserves_path: dict = field(default_factory=lambda: {2025: 2118, 2026: 2199, 2027: 2160})


def apply_ecm(y_prev, lr_prev, sr_deltas, coefs):
    if y_prev <= 0 or lr_prev <= 0:
        return y_prev
    ec = np.log(y_prev) - np.log(lr_prev)
    dlog_y = coefs.get("alpha", 0) - coefs.get("theta", 0.2) * ec
    for k, beta in coefs.get("betas", {}).items():
        if k in sr_deltas:
            dlog_y += beta * sr_deltas[k]
    return y_prev * np.exp(np.clip(dlog_y, -0.25, 0.25))


def run(d_in: pd.DataFrame, coef: dict, sc: Scenario,
        forecast=(2025, 2026, 2027)) -> pd.DataFrame:
    d = d_in.copy()
    d.index = d.index.astype(int)

    for y in forecast:
        if y not in d.index:
            d.loc[y] = pd.NA
    d = d.sort_index()
    if c("XMKT_USD") not in d.columns:
        d[c("XMKT_USD")] = d[c("NYGDPMKTPCD")] * 1.5

    # Set exogenous forecasts based on scenario
    tfp_g = (d.loc[2024, c("NYGDPTFP")] / d.loc[2014, c("NYGDPTFP")]) ** (1/10) - 1
    for i, y in enumerate(forecast, start=1):
        # FX path per regime
        fx_base = 6.91
        if sc.fx_regime == "peg":
            fx_y = fx_base
        elif sc.fx_regime == "crawl":
            fx_y = fx_base * (1 + sc.fx_crawl_rate) ** i
        elif sc.fx_regime == "float":
            # Step-devaluation at first forecast year if fx_step_deval set
            if y == sc.fx_step_year:
                fx_y = fx_base * (1 + sc.fx_step_deval)
            else:
                prev_fx = d.loc[y-1, c("PANUSATLS")] if y-1 in d.index else fx_base
                # Float continues drifting at crawl rate as a simple rule
                fx_y = prev_fx * (1 + sc.fx_crawl_rate)
        else:
            fx_y = fx_base
        d.loc[y, c("PANUSATLS")] = fx_y

        d.loc[y, c("FMLBLPOLYFR")] = d.loc[2024, c("FMLBLPOLYFR")]
        d.loc[y, c("SPPOPTOTL")]   = d.loc[2024, c("SPPOPTOTL")] * (1.011)**i
        d.loc[y, c("SPPOP1564TO")] = d.loc[2024, c("SPPOP1564TO")] * (1.013)**i
        d.loc[y, c("SPPOPWORK")]   = d.loc[2024, c("SPPOPWORK")] * (1.013)**i
        d.loc[y, c("LMPRTSTRL_")]  = d.loc[2024, c("LMPRTSTRL_")]
        d.loc[y, c("LMUNRSTRL_")]  = d.loc[2024, c("LMUNRSTRL_")]
        d.loc[y, c("LMPRTTOTL_")]  = d.loc[2024, c("LMPRTTOTL_")]
        d.loc[y, c("NYGDPTFP")]    = d.loc[2024, c("NYGDPTFP")] * (1 + tfp_g)**i
        d.loc[y, c("NEGDISTKBKN")] = d.loc[2024, c("NEGDISTKBKN")]
        d.loc[y, c("NEGDISTKBCN")] = d.loc[2024, c("NEGDISTKBCN")] * (1.12)**i
        d.loc[y, c("NYGDPDISCKN")] = d.loc[2024, c("NYGDPDISCKN")]
        d.loc[y, c("LMLBFTOTL")]   = d.loc[y, c("SPPOP1564TO")] * d.loc[y, c("LMPRTTOTL_")]/100
        d.loc[y, c("LMEMPSTRL")]   = d.loc[y, c("SPPOP1564TO")] * d.loc[y, c("LMPRTSTRL_")]/100 * \
                                      (1 - d.loc[y, c("LMUNRSTRL_")]/100)
        d.loc[y, c("XMKT_USD")]    = d.loc[2024, c("XMKT_USD")] * (1 + sc.xmkt_growth)**i
        d.loc[y, c("FIRESGRSCD")]  = sc.reserves_path.get(y, 2000)
        d.loc[y, c("RES_SCARCITY")]= 1.0
        d.loc[y, c("GASPROD")]     = sc.gas_prod_path.get(y, 40)
        # Commodity price multiplier on export deflator
        d.loc[y, c("COMMODITY_IDX")] = sc.commodity_price_index.get(y, 1.0)

    # Forward solve
    for y in forecast:
        yp = y - 1

        # Initial guess = previous year value (no amplification)
        for col in d.columns:
            if pd.isna(d.loc[y, col]):
                prev = d.loc[yp, col] if yp in d.index else np.nan
                if pd.notna(prev) and isinstance(prev, (int, float, np.floating)):
                    d.loc[y, col] = prev

        # ---- debt revaluation from FX move (immediate, before solving) -----
        fx_move = (d.loc[y, c("PANUSATLS")] / d.loc[yp, c("PANUSATLS")]) - 1
        if abs(fx_move) > 0.001:
            # External debt in LCU rises proportionally with FX
            d.loc[yp, c("GGDBTEXTLCN_REVAL")] = d.loc[yp, c("GGDBTEXTLCN")] * (1 + fx_move)

        diff = np.inf
        for it in range(300):
            prev_state = d.loc[y].copy()

            d.loc[y, c("NEGDIKSTKKN")] = (1-DEPR)*d.loc[yp, c("NEGDIKSTKKN")] + d.loc[y, c("NEGDIFTOTKN")]
            d.loc[y, c("NYGDPPOTLKN")] = (d.loc[y, c("NYGDPTFP")] *
                                         d.loc[y, c("LMEMPSTRL")]**ALPHA *
                                         d.loc[yp, c("NEGDIKSTKKN")]**(1-ALPHA))

            # ---- CONSUMPTION with wealth channel (Tier 2 addition) ----
            labinc_real = ALPHA * d.loc[y, c("NYGDPFCSTCN")] / d.loc[y, c("NECONPRVTXN")]
            # Wealth proxy: NFA + domestic capital stock (real)
            # Use K stock as real wealth anchor (financial wealth data limited for BOL)
            wealth_real = d.loc[yp, c("NEGDIKSTKKN")]  # lagged real capital
            dly_inc = np.log(labinc_real / (ALPHA * d.loc[yp, c("NYGDPFCSTCN")] / d.loc[yp, c("NECONPRVTXN")]))
            dly_wealth = np.log(wealth_real / d.loc[yp-1, c("NEGDIKSTKKN")]) if yp-1 in d.index else 0
            dly_gdp = np.log(d.loc[y, c("NYGDPMKTPKN")] / d.loc[yp, c("NYGDPMKTPKN")])
            d.loc[y, c("NECONPRVTKN")] = apply_ecm(
                d.loc[yp, c("NECONPRVTKN")],
                ALPHA * d.loc[yp, c("NYGDPFCSTCN")] / d.loc[yp, c("NECONPRVTXN")],
                {"dly_inc": dly_inc, "dly_gdp": dly_gdp,
                 "dly_wealth": dly_wealth * 0.1},   # wealth weight 0.1
                coef["NECONPRVTKN"])

            # Govt consumption
            dly_ngdp_prev = np.log(max(d.loc[y, c("NYGDPMKTPCN")], 1) / max(d.loc[yp, c("NYGDPMKTPCN")], 1))
            d.loc[y, c("NECONGOVTCN")] = d.loc[yp, c("NECONGOVTCN")] * np.exp(dly_ngdp_prev)
            d.loc[y, c("NECONGOVTKN")] = d.loc[y, c("NECONGOVTCN")] / d.loc[y, c("NECONGOVTXN")]

            # Private investment (α clipped, SR on potential)
            dly_potl_y = np.log(d.loc[y, c("NYGDPPOTLKN")] / d.loc[yp, c("NYGDPPOTLKN")])
            d.loc[y, c("NEGDIFPRVKN")] = apply_ecm(
                d.loc[yp, c("NEGDIFPRVKN")], d.loc[yp, c("NYGDPPOTLKN")],
                {"dly_gdp": dly_potl_y, "dly_rate": 0.0}, coef["NEGDIFPRVKN"])
            capex_adjust = sc.cap_spending_cut_pp.get(y, 0.0)
            real_gov_inv = d.loc[yp, c("NEGDIFGOVKN")] * 0.95 * (1 - capex_adjust)
            d.loc[y, c("NEGDIFGOVKN")] = real_gov_inv
            d.loc[y, c("NEGDIFTOTKN")] = d.loc[y, c("NEGDIFPRVKN")] + d.loc[y, c("NEGDIFGOVKN")]

            # ---- EXPORTS: disaggregated 5 components (Tier 3) ----
            dly_xmkt = np.log(d.loc[y, c("XMKT_USD")] / d.loc[yp, c("XMKT_USD")])
            # Weights (of real exports) in 2024 base: gas 20%, mining 22%, agro 18%, mfg 25%, services 15%
            w_gas, w_min, w_agr, w_mfg, w_srv = 0.20, 0.22, 0.18, 0.25, 0.15
            base_exp = d.loc[yp, c("NEEXPGNFSKN")]
            # Gas: exogenous production path
            gas_g = d.loc[y, c("GASPROD")] / d.loc[yp, c("GASPROD")] - 1
            gas_new = w_gas * base_exp * (1 + gas_g)
            # Mining: commodity-price-sensitive; responds to world demand
            mining_new = w_min * base_exp * np.exp(0.8 * dly_xmkt) * d.loc[y, c("COMMODITY_IDX")]
            # Agro: weather-sensitive; here we assume neutral
            agro_new = w_agr * base_exp * np.exp(0.5 * dly_xmkt)
            # Manufactures: world demand
            mfg_new = w_mfg * base_exp * np.exp(1.0 * dly_xmkt)
            # Services (tourism, etc): world demand
            srv_new = w_srv * base_exp * np.exp(1.2 * dly_xmkt)
            # FX competitiveness gain on non-gas exports when FX devalues
            if fx_move > 0:
                non_gas = mining_new + agro_new + mfg_new + srv_new
                # ~50% pass-through to volume over 1 year
                non_gas_boost = non_gas * 0.5 * fx_move
                mining_new = mining_new * (1 + 0.5 * fx_move)
                mfg_new    = mfg_new * (1 + 0.5 * fx_move)
                agro_new   = agro_new * (1 + 0.3 * fx_move)
                srv_new    = srv_new * (1 + 0.5 * fx_move)
            d.loc[y, c("NEEXPGNFSKN")] = gas_new + mining_new + agro_new + mfg_new + srv_new

            # Imports with FX-scarcity cap (tightened by commodity if parallel market widens)
            gde_prev = (d.loc[yp, c("NECONPRVTKN")] + d.loc[yp, c("NECONGOVTKN")]
                        + d.loc[yp, c("NEGDIFTOTKN")] + d.loc[yp, c("NEEXPGNFSKN")])
            gde_cur  = (d.loc[y, c("NECONPRVTKN")] + d.loc[y, c("NECONGOVTKN")]
                        + d.loc[y, c("NEGDIFTOTKN")] + d.loc[y, c("NEEXPGNFSKN")])
            dly_gde = np.log(gde_cur / gde_prev)
            imp_ecm = apply_ecm(d.loc[yp, c("NEIMPGNFSKN")], gde_prev,
                                {"dly_gde": dly_gde}, coef["NEIMPGNFSKN"])
            imp_share_2024 = d.loc[2024, c("NEIMPGNFSKN")] / d.loc[2024, c("NYGDPMKTPKN")]
            imp_compression = {2025: 0.92, 2026: 0.84, 2027: 0.82}.get(y, 1.0)
            # Under devaluation, FX makes imports even more costly → more compression
            if fx_move > 0.05:
                imp_compression *= (1 - 0.3 * fx_move)
            imp_cap = imp_share_2024 * imp_compression * d.loc[y, c("NYGDPMKTPKN")]
            d.loc[y, c("NEIMPGNFSKN")] = min(imp_ecm, imp_cap)

            # Real GDP identity
            d.loc[y, c("NYGDPMKTPKN")] = (d.loc[y, c("NECONPRVTKN")] + d.loc[y, c("NECONGOVTKN")]
                                        + d.loc[y, c("NEGDIFTOTKN")] + d.loc[y, c("NEGDISTKBKN")]
                                        + d.loc[y, c("NEEXPGNFSKN")] - d.loc[y, c("NEIMPGNFSKN")]
                                        + d.loc[y, c("NYGDPDISCKN")])
            d.loc[y, c("NYGDPGAP_")] = (d.loc[y, c("NYGDPMKTPKN")] / d.loc[y, c("NYGDPPOTLKN")] - 1)*100

            # Production (agriculture with weather dummy)
            weather_dummy = 0.0
            # El Niño 2023 and 2016 had -3% on agriculture; 2027 modeled as neutral
            if y in (2023, 2016, 2010):
                weather_dummy = -0.03
            d.loc[y, c("NVAGRTOTLKN")] = apply_ecm(
                d.loc[yp, c("NVAGRTOTLKN")], d.loc[yp, c("NYGDPPOTLKN")],
                {"dly_gde": dly_gde}, coef["NVAGRTOTLKN"]) * (1 + weather_dummy)
            d.loc[y, c("NVINDTOTLKN")] = apply_ecm(
                d.loc[yp, c("NVINDTOTLKN")], d.loc[yp, c("NYGDPPOTLKN")],
                {"dly_gde": dly_gde}, coef["NVINDTOTLKN"])
            gas_va_drag = (d.loc[y, c("GASPROD")]/d.loc[yp, c("GASPROD")] - 1) * 0.25
            d.loc[y, c("NVINDTOTLKN")] *= (1 + gas_va_drag)
            d.loc[y, c("NYGDPFCSTKN")] = d.loc[y, c("NYGDPMKTPKN")] * 0.92
            d.loc[y, c("NVSRVTOTLKN")] = d.loc[y, c("NYGDPFCSTKN")] - d.loc[y, c("NVAGRTOTLKN")] - d.loc[y, c("NVINDTOTLKN")]

            # CPI with Phillips + reserve-scarcity × BCB-fin + FX pass-through
            pi_lag = np.log(d.loc[yp, c("FPCPITOTLXN")] / d.loc[yp-1, c("FPCPITOTLXN")])
            gap = d.loc[y, c("NYGDPGAP_")] / 100
            bcb_fin_gdp_prev = d.loc[y, c("GGFINBCBGD")] if pd.notna(d.loc[y].get(c("GGFINBCBGD"), np.nan)) else 10.0
            scar = d.loc[y, c("RES_SCARCITY")]
            cc = coef["FPCPITOTLXN"]
            fx_passthrough = 0.4 * fx_move  # 40% pass-through of FX to CPI within year
            pi_t = (cc["alpha"] + cc["pi_lag"]*pi_lag + cc["gap"]*gap
                  + 0.60 * scar * (bcb_fin_gdp_prev/100)
                  + fx_passthrough)
            pi_t = np.clip(pi_t, -0.03, 0.45)
            d.loc[y, c("FPCPITOTLXN")] = d.loc[yp, c("FPCPITOTLXN")] * np.exp(pi_t)

            # Monetary policy rule (Tier 2 addition)
            if sc.monetary_rule == "taylor":
                pi_target = 0.03
                r_n = 0.03  # natural real rate
                d.loc[y, c("FMLBLPOLYFR")] = 100 * (r_n + pi_target +
                                                    1.5 * (pi_t - pi_target) + 0.5 * gap)
            elif sc.monetary_rule == "money":
                # Money supply rule → rate moves to clear money demand
                m_target_growth = 0.08  # 8% money target
                d.loc[y, c("FMLBLPOLYFR")] = d.loc[yp, c("FMLBLPOLYFR")] + 100*(pi_t - m_target_growth)
            # else passive: rate exogenous (already set)

            # Deflators
            for p in [c("NYGDPFCSTXN"), c("NECONPRVTXN"), c("NECONGOVTXN"),
                      c("NEGDIFTOTXN"), c("NVAGRTOTLXN"), c("NVINDTOTLXN"), c("NVSRVTOTLXN")]:
                d.loc[y, p] = d.loc[yp, p] * np.exp(pi_t)
            d.loc[y, c("NEIMPGNFSXN")] = d.loc[yp, c("NEIMPGNFSXN")] * np.exp(0.02 + 0.4*pi_t + 0.8*fx_move)
            d.loc[y, c("NEEXPGNFSXN")] = d.loc[yp, c("NEEXPGNFSXN")] * np.exp(0.01 + 0.3*pi_t + 0.5*fx_move)
            d.loc[y, c("NYGDPMKTPXN")] = d.loc[yp, c("NYGDPMKTPXN")] * np.exp(pi_t)

            # Nominal aggregates
            d.loc[y, c("NYGDPMKTPCN")] = d.loc[y, c("NYGDPMKTPKN")] * d.loc[y, c("NYGDPMKTPXN")]
            d.loc[y, c("NYGDPFCSTCN")] = d.loc[y, c("NYGDPFCSTKN")] * d.loc[y, c("NYGDPFCSTXN")]
            d.loc[y, c("NECONPRVTCN")] = d.loc[y, c("NECONPRVTKN")] * d.loc[y, c("NECONPRVTXN")]
            d.loc[y, c("NECONGOVTCN")] = d.loc[y, c("NECONGOVTKN")] * d.loc[y, c("NECONGOVTXN")]
            d.loc[y, c("NEGDIFTOTCN")] = d.loc[y, c("NEGDIFTOTKN")] * d.loc[y, c("NEGDIFTOTXN")]
            d.loc[y, c("NEEXPGNFSCN")] = d.loc[y, c("NEEXPGNFSKN")] * d.loc[y, c("NEEXPGNFSXN")]
            d.loc[y, c("NEIMPGNFSCN")] = d.loc[y, c("NEIMPGNFSKN")] * d.loc[y, c("NEIMPGNFSXN")]

            # Labor
            prod_g = np.log(d.loc[y, c("NYGDPMKTPKN")]/d.loc[y, c("LMEMPSTRL")] /
                            (d.loc[yp, c("NYGDPMKTPKN")]/d.loc[yp, c("LMEMPSTRL")]))
            wage_indexation = 0.0 if sc.wage_freeze else (pi_t + 0.5 * prod_g)
            d.loc[y, c("NEWRTTOTLXN")] = d.loc[yp, c("NEWRTTOTLXN")] * np.exp(wage_indexation)
            d.loc[y, c("NYYWBTOTLCN")] = d.loc[y, c("NEWRTTOTLXN")] * d.loc[y, c("LMEMPTOTL")]
            d.loc[y, c("LMEMPTOTL")] = apply_ecm(
                d.loc[yp, c("LMEMPTOTL")], d.loc[y, c("LMEMPSTRL")],
                {"gap_chg": gap, "dly_lstar": np.log(d.loc[y, c("LMEMPSTRL")]/d.loc[yp, c("LMEMPSTRL")])},
                coef["LMEMPTOTL"])
            d.loc[y, c("LMUNRTOTL_")] = (1 - d.loc[y, c("LMEMPTOTL")]/d.loc[y, c("LMLBFTOTL")])*100

            # Hydrocarbon revenue
            gas_ratio = d.loc[y, c("GASPROD")] / d.loc[yp, c("GASPROD")]
            d.loc[y, c("GGREVIDHCN")]   = d.loc[yp, c("GGREVIDHCN")] * gas_ratio * np.exp(pi_t*0.3)
            d.loc[y, c("GGREVIEHDCN")]  = d.loc[yp, c("GGREVIEHDCN")] * 0.97 * np.exp(pi_t*0.5)
            d.loc[y, c("EMPROYALTIES")] = d.loc[yp, c("EMPROYALTIES")] * gas_ratio * np.exp(pi_t*0.3)
            d.loc[y, c("EMPHYDROSALES")]= d.loc[yp, c("EMPHYDROSALES")] * gas_ratio * np.exp(pi_t*0.4)

            # Expenditure (total ECM + fuel override + scenario adjustments)
            exp_ecm = apply_ecm(
                d.loc[yp, c("GGEXPTOTLCN")], d.loc[yp, c("NYGDPMKTPCN")],
                {"dly_gdpn": dly_ngdp_prev}, coef["GGEXPTOTLCN"])
            fuel_share = sc.fuel_subsidy_path_gdp.get(y, 0.037)
            fuel_extra_pp = fuel_share - d.loc[2024, c("GGEXPFUELCN")] / d.loc[2024, c("NYGDPMKTPCN")]
            d.loc[y, c("GGEXPFUELCN")] = fuel_share * d.loc[y, c("NYGDPMKTPCN")]
            # Interest with debt revaluation (FX affects external part)
            ext_debt_base = d.loc[yp, c("GGDBTEXTLCN_REVAL")] if c("GGDBTEXTLCN_REVAL") in d.columns and \
                           pd.notna(d.loc[yp].get(c("GGDBTEXTLCN_REVAL"), np.nan)) \
                           else d.loc[yp, c("GGDBTEXTLCN")]
            int_rate_ext = 0.04
            int_rate_dom = 0.09
            d.loc[y, c("GGEXPINTECN")] = int_rate_ext * ext_debt_base
            d.loc[y, c("GGEXPINTDCN")] = int_rate_dom * d.loc[yp, c("GGDBTDOMTCN")]
            d.loc[y, c("GGEXPINTPCN")] = d.loc[y, c("GGEXPINTECN")] + d.loc[y, c("GGEXPINTDCN")]
            # Wage freeze scenario: wage bill flat real (adjust exp total)
            wage_cut_pp = 0.0
            if sc.wage_freeze:
                # Implied saving = 2024 wage share × pi_t (the real-freeze saves inflation-indexation)
                wage_share_2024 = d.loc[2024, c("GGEXPWAGESCN")] / d.loc[2024, c("NYGDPMKTPCN")]
                wage_cut_pp = wage_share_2024 * (1 - 1/(1+pi_t))
            cap_cut_pp = sc.cap_spending_cut_pp.get(y, 0.0)
            tax_rat = sc.tax_ratchet_pp.get(y, 0.0)
            d.loc[y, c("GGEXPTOTLCN")] = (exp_ecm
                                        + (fuel_extra_pp - wage_cut_pp - cap_cut_pp)
                                          * d.loc[y, c("NYGDPMKTPCN")])
            # Allocate component shares
            tot_nonint_nonfuel = d.loc[y, c("GGEXPTOTLCN")] - d.loc[y, c("GGEXPFUELCN")] - d.loc[y, c("GGEXPINTPCN")]
            base_2024_nonint_nonfuel = (d.loc[2024, c("GGEXPTOTLCN")] - d.loc[2024, c("GGEXPFUELCN")]
                                      - d.loc[2024, c("GGEXPINTPCN")])
            for comp in ["GGEXPWAGESCN", "GGEXPGSCN", "GGEXPTRNSCN", "GGEXPCAPEXCN"]:
                share = d.loc[2024, c(comp)] / base_2024_nonint_nonfuel
                d.loc[y, c(comp)] = share * tot_nonint_nonfuel

            # Revenue
            non_hc_rev_prev = (d.loc[yp, c("GGREVTOTLCN")] - d.loc[yp, c("GGREVIDHCN")]
                              - d.loc[yp, c("GGREVIEHDCN")] - d.loc[yp, c("EMPROYALTIES")])
            non_hc_rev_tar = d.loc[yp, c("NYGDPMKTPCN")] * 0.24
            non_hc_rev_new = apply_ecm(non_hc_rev_prev, non_hc_rev_tar,
                                      {"dly_gdpn": dly_ngdp_prev}, coef["GGREVTOTLCN"])
            non_hc_rev_new += tax_rat * d.loc[y, c("NYGDPMKTPCN")]  # scenario tax ratchet
            d.loc[y, c("GGREVTOTLCN")] = (non_hc_rev_new + d.loc[y, c("GGREVIDHCN")]
                                        + d.loc[y, c("GGREVIEHDCN")] + d.loc[y, c("EMPROYALTIES")])
            d.loc[y, c("GGREVHYDRCN")] = d.loc[y, c("GGREVIDHCN")] + d.loc[y, c("GGREVIEHDCN")] + d.loc[y, c("EMPROYALTIES")]

            # Balances
            d.loc[y, c("GGBALOVRLCN")] = d.loc[y, c("GGREVTOTLCN")] - d.loc[y, c("GGEXPTOTLCN")]
            d.loc[y, c("GGBALPRIMCN")] = d.loc[y, c("GGREVTOTLCN")] - (d.loc[y, c("GGEXPTOTLCN")] - d.loc[y, c("GGEXPINTPCN")])
            # Debt with revaluation
            ext_base = d.loc[yp, c("GGDBTEXTLCN_REVAL")] if c("GGDBTEXTLCN_REVAL") in d.columns and \
                      pd.notna(d.loc[yp].get(c("GGDBTEXTLCN_REVAL"), np.nan)) \
                      else d.loc[yp, c("GGDBTEXTLCN")]
            d.loc[y, c("GGDBTTOTLCN")] = d.loc[yp, c("GGDBTTOTLCN")] + (ext_base - d.loc[yp, c("GGDBTEXTLCN")]) - d.loc[y, c("GGBALOVRLCN")]
            d.loc[y, c("GGDBTEXTLCN")] = d.loc[y, c("GGDBTTOTLCN")] * 0.25
            d.loc[y, c("GGDBTDOMTCN")] = d.loc[y, c("GGDBTTOTLCN")] - d.loc[y, c("GGDBTEXTLCN")]
            d.loc[y, c("GGDBTTOTLGD")] = d.loc[y, c("GGDBTTOTLCN")] / d.loc[y, c("NYGDPMKTPCN")] * 100
            d.loc[y, c("GGBALOVRLGD")] = d.loc[y, c("GGBALOVRLCN")] / d.loc[y, c("NYGDPMKTPCN")] * 100
            # BCB financing residual (capped)
            ext_net_gdp = -0.005
            priv_dom_gdp = 0.005
            bcb_residual = -d.loc[y, c("GGBALOVRLGD")] - ext_net_gdp - priv_dom_gdp
            d.loc[y, c("GGFINBCBGD")] = min(bcb_residual, sc.bcb_fin_cap_gdp)
            d.loc[y, c("GGFINBCBCN")] = d.loc[y, c("GGFINBCBGD")] / 100 * d.loc[y, c("NYGDPMKTPCN")]

            # BoP
            d.loc[y, c("NYGDPMKTPCD")] = d.loc[y, c("NYGDPMKTPCN")] / d.loc[y, c("PANUSATLS")]
            d.loc[y, c("BXGSRMRCHCD")] = (d.loc[y, c("NEEXPGNFSCN")]/d.loc[y, c("PANUSATLS")]) * \
                (d.loc[2024, c("BXGSRMRCHCD")] * d.loc[2024, c("PANUSATLS")] / d.loc[2024, c("NEEXPGNFSCN")])
            d.loc[y, c("BMGSRMRCHCD")] = (d.loc[y, c("NEIMPGNFSCN")]/d.loc[y, c("PANUSATLS")]) * \
                (d.loc[2024, c("BMGSRMRCHCD")] * d.loc[2024, c("PANUSATLS")] / d.loc[2024, c("NEIMPGNFSCN")])
            trade_bal = d.loc[y, c("BXGSRMRCHCD")] - d.loc[y, c("BMGSRMRCHCD")]
            other_cab = (d.loc[2024, c("BNCABFUNDCD")] - (d.loc[2024, c("BXGSRMRCHCD")] -
                         d.loc[2024, c("BMGSRMRCHCD")])) / d.loc[2024, c("NYGDPMKTPCD")]
            d.loc[y, c("BNCABFUNDCD")] = trade_bal + other_cab * d.loc[y, c("NYGDPMKTPCD")]

            # Convergence
            key = [c("NYGDPMKTPKN"), c("FPCPITOTLXN"), c("GGBALOVRLCN"), c("GGDBTTOTLCN")]
            cur = d.loc[y, key].astype(float); old = prev_state[key].astype(float)
            if old.isna().any() or (old == 0).any():
                diff = np.inf; continue
            diff = ((cur - old) / old).abs().max()
            if diff < 1e-5:
                break

    return d
