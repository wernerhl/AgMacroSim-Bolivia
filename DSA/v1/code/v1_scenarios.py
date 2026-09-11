# -*- coding: utf-8 -*-
"""v1_scenarios.py — S9 (ISAE near-term baseline), S10 (disinflation-repricing success), and the
right-sized contingent-liability restatement of S6. Reuses the DSA reduced-form core unchanged.
Every debt figure at official and market valuation. Seed 20260910 (inherited; no new stochastic step)."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "DSA", "code"))
sys.path.insert(0, "/Users/whl/Documents/whl.BolBudget/MFMOD_BOL/DSA/code")
import dsa_core as C
OUT=os.path.join(os.path.dirname(__file__),"..")

def path_row(rec):
    return {r["year"]:(round(r["b_off"],1),round(r["b_mkt"],1)) for r in rec}

res={}

# ---- S0 reference ----
p,de,cl,_=C.scen("S0"); res["S0"]=path_row(C.run(p,de_override=de,sfa_cl=cl))

# ---- S9 ISAE near-term baseline: replace 2026 growth with ISAE reads; 2028+ MEFP (flagged) ----
def s9(g2026):
    p=C.base_paths(); p["G"][2026]=g2026
    return C.run(p)
res["S9_central"]=path_row(s9(-2.8))      # ISAE central window read
res["S9_upper"]  =path_row(s9(-1.4))      # fire-adjusted upper
res["S9_lower"]  =path_row(s9(-6.0))      # decree lower bound

# ---- S10 disinflation-repricing success: effective rate converges to market marginal as stock rolls off
# (GFN 20-25%/yr => ~20-25% reprices annually). Inflation at baseline single-digit path. ----
p=C.base_paths()
p["RNOM"]={2025:2.8,2026:3.2,2027:4.5,2028:6.0,2029:7.5,2030:8.3,2031:8.6,2032:8.7,2033:8.8,2034:8.9,2035:9.0}
rec10=C.run(p); res["S10"]=path_row(rec10)
# r-g crossing year and stabilizing surplus
s10_detail=[]
for r in rec10:
    s10_detail.append((r["year"], round(r["rminusg"],2), round(r["pb_star"],2), round(r["b_off"],1), round(r["b_mkt"],1)))
res["S10_detail"]=s10_detail
cross=next((y for y,rg,_,_,_ in s10_detail if rg>0), None)
res["S10_rg_crossing_year"]=cross
res["S10_surplus_needed"]=next((pbs for y,rg,pbs,_,_ in s10_detail if y==(cross or 2035)), None)

# ---- S6 right-sized contingent liabilities: range from known components ----
# components (share of GDP, official): YPFB fuel-trader arrears ~2.0; residual arrears/deuda flotante ~0.9
# (MEFP p.5); SOE operating losses (754-entity universe, financials pending) ~1-3; CPVIS wind-down ~1-3;
# Gestora public-sector exposure (near-term crystallization) ~0-3. Lower/central/upper bundle:
def s6(size, split=(0.55,0.45)):
    s={y:0.0 for y in C.YEARS}; s[2027]=size*split[0]; s[2028]=size*split[1]
    return C.run(C.base_paths(), sfa_cl=s)
res["S6_low"]  =path_row(s6(4.0))
res["S6_central"]=path_row(s6(7.0))
res["S6_high"] =path_row(s6(12.0))

json.dump(res, open(os.path.join(OUT,"outputs","v1_scenarios.json"),"w"), indent=1, default=float)

# ---- console report ----
def line(tag,row,yrs=(2026,2027,2028,2029,2031,2035)):
    print(f"  {tag:16} "+" ".join(f"{row[y][0]:.0f}/{row[y][1]:.0f}" for y in yrs))
print("debt %GDP (official/market)      2026    2027    2028    2029    2031    2035")
for k in ["S0","S9_upper","S9_central","S9_lower","S10","S6_low","S6_central","S6_high"]:
    line(k,res[k])
print(f"\nS9 central: 2029 debt {res['S9_central'][2029][0]:.0f}/{res['S9_central'][2029][1]:.0f} "
      f"vs S0 {res['S0'][2029][0]:.0f}/{res['S0'][2029][1]:.0f}; cushion to 90 (market) "
      f"{90-res['S9_central'][2029][1]:.1f}pp vs {90-res['S0'][2029][1]:.1f}pp under S0")
print(f"S10 r-g turns positive in {cross}; stabilizing primary then {res['S10_surplus_needed']:+.2f}% GDP; "
      f"debt stops falling around then (2031 {res['S10'][2031][0]:.0f}/{res['S10'][2031][1]:.0f}, "
      f"2035 {res['S10'][2035][0]:.0f}/{res['S10'][2035][1]:.0f})")
print(f"S6 right-sized: 2028 debt at CL=4%: {res['S6_low'][2028][0]:.0f}/{res['S6_low'][2028][1]:.0f}; "
      f"7%: {res['S6_central'][2028][0]:.0f}/{res['S6_central'][2028][1]:.0f}; "
      f"12%: {res['S6_high'][2028][0]:.0f}/{res['S6_high'][2028][1]:.0f}")
