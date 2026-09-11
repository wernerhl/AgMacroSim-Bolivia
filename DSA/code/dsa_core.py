# -*- coding: utf-8 -*-
"""
dsa_core.py — reduced-form debt-dynamics engine for the Bolivia MFMod-BOL DSA under the IMF/MEFP.
Identity (Appendix A of the work order):
    b_t = ((1+r_t)/(1+g_t)) b_{t-1} - pb_t + sfa_t
    sfa_FX,t = share_FX * b_{t-1} * (de_t/(1+de_t)) ; contingent liabilities enter as a switched sfa term.
All ratios reported at BOTH the official peg valuation and the market/parallel valuation.
r = effective REAL interest rate on the debt (coupon-based, FX revaluation kept OUT of r and IN sfa_FX).
Baseline paths are MEFP-anchored (page cites in outputs/00_registry.md and 01_baseline.md);
everything downstream of the cited anchors is labelled program-consistent or reduced-form.
Seed for stochastic steps: 20260910.
"""
import json, csv, os
SEED = 20260910
OUT = os.path.join(os.path.dirname(__file__), "..")
YEARS = list(range(2025, 2036))              # 2025 (anchor) .. 2035

# ---------------------------------------------------------------- baseline S0 (MEFP-anchored)
# Nominal GDP anchor: 2026 deficit cap Bs47.0bn = 9.3% GDP (MEFP p.5) -> GDP2026=505.4; 2025 overall
# -50.9bn = ~11% GDP (p.1) -> GDP2025~447. Debt ratio anchored directly at MEFP p.8-9: 80 official / 90 market.
B0_OFFICIAL = 80.0                            # SPNF debt %GDP end-2025, peg valuation (MEFP p.8, para 21)
B0_MARKET   = 90.0                            # SPNF debt %GDP end-2025, market valuation (MEFP p.8, para 21)
FX_SHARE    = 0.31                            # external/FX share of debt (24.6%GDP ext / ~80% total; ">1/3" p.8)
E_PEG       = 6.96                            # official peg Bs/USD
E_UNIF      = 9.80                            # unified/reference rate that reconciles the 90% market figure end-2025
E_PARALLEL  = 13.50                           # street parallel rate (central of 1.7-2.2x band on USD-GDP)

# Real GDP growth (%): 2025 -1.6 CITED (MEFP p.2 para4). 2026 contraction, 2027 trough, 2028 recovery
# (MEFP p.3 para7, qualitative) -> the numeric 2026-2035 path is PROGRAM-CONSISTENT, not a MEFP figure.
G = {2025:-1.6, 2026:-1.0, 2027:-0.5, 2028:1.5, 2029:2.5, 2030:3.0, 2031:3.0, 2032:3.0, 2033:3.0, 2034:3.0, 2035:3.0}
# GDP deflator ~ CPI (%): 2026 14 CITED (p.10 para24); 2025 peak, single digit by 2028 (p.3).
PI = {2025:15.0, 2026:14.0, 2027:10.0, 2028:7.0, 2029:5.0, 2030:4.0, 2031:4.0, 2032:4.0, 2033:4.0, 2034:4.0, 2035:4.0}
# Primary balance %GDP: 2025 -39.6bn/447=-8.9, 2026 -33.0bn/505=-6.5 (Cuadro 1 p.17); glide to ZERO by 2029
# (QPC, MEFP p.5 para11); 2027-2028 program glide. From 2029 held at programmed zero.
PB = {2025:-8.9, 2026:-6.5, 2027:-3.5, 2028:-1.7, 2029:0.0, 2030:0.0, 2031:0.0, 2032:0.0, 2033:0.0, 2034:0.0, 2035:0.0}
# Effective NOMINAL interest rate on the debt (%): 2024 actual ~2.6% (concessional). Rises as the peg-era
# concessional stock is diluted by the USD1bn bond (p.2) and local-currency issuance. Reduced-form path.
RNOM = {2025:2.8, 2026:3.0, 2027:3.4, 2028:3.8, 2029:4.2, 2030:4.5, 2031:4.6, 2032:4.7, 2033:4.8, 2034:4.9, 2035:5.0}
# Official-rate depreciation de_t (FX-unification): the peg unifies mid-2026 (p.9 para23) -> a one-off
# official-rate step in 2026 that mechanically revalues FX debt (p.3 para7). de as fraction.
DE_OFFICIAL = {y:0.0 for y in YEARS}; DE_OFFICIAL[2026] = (E_UNIF-E_PEG)/E_PEG    # ~0.408 in 2026
# Amortization (share of prior stock coming due): external multilateral long (p.9 ~70% multilateral) -> low;
# domestic short. Reduced-form. GFN = amort + interest + overall deficit.
AMORT_EXT = 0.05        # 5%/yr of external (FX) stock
AMORT_DOM = 0.22        # 22%/yr of domestic stock (short domestic market)

def real_rate(rnom, pi): return (1+rnom/100.0)/(1+pi/100.0) - 1.0

# ---------------------------------------------------------------- the engine
def run(paths, b0_off=B0_OFFICIAL, b0_mkt=B0_MARKET, fx_share=FX_SHARE,
        sfa_cl=None, de_override=None, amort_ext=AMORT_EXT, amort_dom=AMORT_DOM):
    """paths: dict of {G,PI,PB,RNOM} year->value. Returns per-year records."""
    G_,PI_,PB_,RNOM_ = paths["G"],paths["PI"],paths["PB"],paths["RNOM"]
    de = de_override if de_override is not None else DE_OFFICIAL
    sfa_cl = sfa_cl or {y:0.0 for y in YEARS}
    b_off, b_mkt = b0_off, b0_mkt
    rec=[]
    for y in YEARS[1:]:                       # evolve 2026..2035 from the 2025 anchor
        g,pi,pb,rn = G_[y],PI_[y],PB_[y],RNOM_[y]
        r = real_rate(rn,pi)*100.0            # real effective rate, %
        # FX revaluation term (only bites the official/peg-valued series when the official rate steps):
        sfa_fx_off = fx_share * b_off * (de[y]/(1+de[y]))            # pp of GDP (b_off already in %, de a fraction)
        # market series already reflects market FX; its incremental FX term is small once unified:
        sfa_fx_mkt = fx_share * b_mkt * (max(0.0,de[y]-DE_OFFICIAL.get(y,0))/(1+de[y]))
        auto = ((r/100.0 - g/100.0)/(1+g/100.0))                     # (r-g)/(1+g)
        b_off_new = b_off*(1+auto) - pb + sfa_fx_off + sfa_cl[y]
        b_mkt_new = b_mkt*(1+auto) - pb + sfa_fx_mkt + sfa_cl[y]
        # stabilizers given this year's r, pb, sfa (official series)
        sfa_tot_off = sfa_fx_off + sfa_cl[y]
        g_star = (r/100.0) - (pb - sfa_tot_off)/b_off               # g that sets db=0 (approx, %/100)
        pb_star = auto*b_off + sfa_tot_off                          # pb that sets db=0, %GDP
        # GFN (official-valued stock): amort + interest + overall deficit
        ext = fx_share*b_off; dom=(1-fx_share)*b_off
        amort = amort_ext*ext + amort_dom*dom
        interest = (rn/100.0)*b_off/(1+ (0 if y==2026 else 0))      # nominal interest %GDP (approx on stock)
        overall_def = -(pb - interest)                              # overall deficit %GDP = interest - pb (pb negative)
        gfn = amort + interest + max(0.0,overall_def)
        rec.append(dict(year=y, g=g, pi=pi, pb=pb, r_real=r, rminusg=r-g,
                        b_off=b_off_new, b_mkt=b_mkt_new,
                        sfa_fx_off=sfa_fx_off, sfa_cl=sfa_cl[y],
                        g_star=g_star*100.0, pb_star=pb_star, gfn=gfn,
                        amort=amort, interest=interest, overall_def=overall_def))
        b_off, b_mkt = b_off_new, b_mkt_new
    return rec

def base_paths(): return {"G":dict(G),"PI":dict(PI),"PB":dict(PB),"RNOM":dict(RNOM)}

# ---------------------------------------------------------------- scenarios S1..S8
def scen(name):
    p=base_paths(); de=dict(DE_OFFICIAL); sfa_cl={y:0.0 for y in YEARS}; note=""
    if name=="S0": note="MEFP baseline"
    elif name=="S1":   # growth shortfall: 2027 trough 1.5 deeper, 2028-29 rebound halved
        p["G"][2027]-=1.5; p["G"][2028]=G[2028]*0.5; p["G"][2029]=G[2029]*0.5; note="growth shortfall"
    elif name=="S2":   # investment compression: 60% of cut on capex; capex->potential growth elasticity
        # consolidation ~8.5%GDP; 60% on capex; elasticity of potential growth to public inv ~0.15
        for y in (2028,2029,2030,2031): p["G"][y]-=0.6; note="investment compression"
    elif name=="S3":   # reform reversal: fuel cost-recovery at 50%, unrest -0.5 growth, pb misses
        p["PB"][2027]-=1.2; p["PB"][2028]-=1.0; p["G"][2027]-=0.5; note="reform reversal / partial fuel"
    elif name=="S4":   # external downside: ToT -10, oil +20, disbursement slip, ext rate +150bp
        for y in YEARS: p["RNOM"][y]+=1.5
        p["PB"][2026]-=0.8; p["PB"][2027]-=0.8; p["G"][2026]-=0.4; note="external downside"
    elif name=="S5":   # second FX adjustment: further 15-20% real deprec in 2027 -> sfa_FX
        de[2027]=0.175; p["PI"][2027]+=4.0; p["PI"][2028]+=2.0; note="second FX adjustment"
    elif name=="S6":   # contingent liabilities: 5-10% GDP crystallize (SOEs/CPVIS/Gestora/arrears)
        sfa_cl[2027]=4.0; sfa_cl[2028]=3.5; note="contingent liabilities +7.5%GDP"
    elif name=="S7":   # combined adverse S1+S2+S3
        p["G"][2027]-=2.0; p["G"][2028]=G[2028]*0.5-0.6; p["G"][2029]=G[2029]*0.5-0.6
        for y in (2030,2031): p["G"][y]-=0.6
        p["PB"][2027]-=1.2; p["PB"][2028]-=1.0; note="combined adverse (S1+S2+S3)"
    elif name=="S8":   # growth-protective: same envelope, cut current not capex, +potential growth from 2028
        for y in (2028,2029,2030,2031): p["G"][y]+=0.6; note="growth-protective (capex ring-fenced)"
    return p,de,sfa_cl,note

def main():
    allrec={}
    for s in ["S0","S1","S2","S3","S4","S5","S6","S7","S8"]:
        p,de,sfa_cl,note=scen(s)
        allrec[s]=dict(note=note, rec=run(p, de_override=de, sfa_cl=sfa_cl))
    os.makedirs(os.path.join(OUT,"data"),exist_ok=True)
    json.dump(allrec, open(os.path.join(OUT,"data","scenarios.json"),"w"), indent=1, default=float)
    # console summary
    print("scenario  2026  2027  2028  2029  2030  2031  | note   (debt %GDP, official valuation)")
    for s,d in allrec.items():
        by={r["year"]:r["b_off"] for r in d["rec"]}
        print(f"  {s:3}  " + " ".join(f"{by[y]:5.1f}" for y in (2026,2027,2028,2029,2030,2031)) + f"  | {d['note']}")
    print("\n(market valuation, S0):", " ".join(f"{r['year']}={r['b_mkt']:.1f}" for r in allrec['S0']['rec'][:5]))
    print("S0 r-g:", " ".join(f"{r['year']}={r['rminusg']:+.1f}" for r in allrec['S0']['rec'][:5]))
    return allrec

if __name__=="__main__": main()
