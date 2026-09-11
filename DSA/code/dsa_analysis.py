# -*- coding: utf-8 -*-
"""dsa_analysis.py — Phases 5-6: stochastic fan, convergence/divergence bifurcation, sensitivity,
stabilizer gaps. Imports the seeded engine in dsa_core. Seed 20260910."""
import numpy as np, json, os, csv
import dsa_core as C
SEED=C.SEED
OUT=os.path.join(os.path.dirname(__file__),"..")
np.random.seed(SEED)

# historical joint (g, r_real), 2002-2024 (computed in build step; embedded so the pipeline is self-contained)
HIST_MEAN=np.array([3.23,-1.99]); HIST_COV=np.array([[22.02,-0.16],[-0.16,8.02]])

def evolve(gpath,rpath,pbpath,b0=C.B0_OFFICIAL,fx=C.FX_SHARE,de=None,sfa_cl=None):
    de=de or C.DE_OFFICIAL; sfa_cl=sfa_cl or {y:0 for y in C.YEARS}
    b=b0; out={C.YEARS[0]:b0}
    for y in C.YEARS[1:]:
        r=rpath[y]/100.0; g=gpath[y]/100.0
        sfa=fx*b*(de[y]/(1+de[y]))+sfa_cl[y]
        b=b*(1+(r-g)/(1+g))-pbpath[y]+sfa; out[y]=b
    return out

def base_real_r():
    return {y:C.real_rate(C.RNOM[y],C.PI[y])*100 for y in C.YEARS}

# ---------- Phase 6: stochastic fan (shocks around baseline, historical covariance) ----------
def fan(scenario="S0",n=1000):
    p,de,sfa_cl,_=C.scen(scenario)
    g_base=p["G"]; pb=p["PB"]; r_base={y:C.real_rate(p["RNOM"][y],p["PI"][y])*100 for y in C.YEARS}
    rng=np.random.default_rng(SEED)
    L=np.linalg.cholesky(HIST_COV)
    paths=[]
    decl_2029=0
    for i in range(n):
        gp=dict(g_base); rp=dict(r_base)
        for y in C.YEARS[1:]:
            eps=L@rng.standard_normal(2)          # (dg, dr) innovation, mean 0, historical cov
            gp[y]=g_base[y]+eps[0]; rp[y]=r_base[y]+eps[1]
        b=evolve(gp,rp,pb,de=de,sfa_cl=sfa_cl)
        paths.append([b[y] for y in C.YEARS])
        if b[2029]<b[2028]: decl_2029+=1
    A=np.array(paths)
    pct={q:np.percentile(A,q,axis=0).tolist() for q in (10,25,50,75,90)}
    return dict(p_declining_2029=decl_2029/n, pct=pct, years=C.YEARS)

# ---------- Phase 5: bifurcation surface (post-2028 growth x capex share of consolidation) ----------
def bifurcation(kappa=1.0):
    g_grid=np.round(np.arange(0.0,4.01,0.25),2)      # post-2028 sustained growth
    c_grid=np.round(np.arange(0.0,1.01,0.1),2)       # capex share of the cut
    r_base=base_real_r()
    Z=np.zeros((len(c_grid),len(g_grid)))            # sign of (b2033-b2029): <0 declining
    for i,c in enumerate(c_grid):
        for j,g2 in enumerate(g_grid):
            gp=dict(C.G)
            for y in (2028,2029,2030,2031,2032,2033,2034,2035): gp[y]=g2-kappa*c
            b=evolve(gp,r_base,C.PB)
            Z[i,j]=b[2033]-b[2029]
    return dict(g_grid=g_grid.tolist(), c_grid=c_grid.tolist(), Z=Z.tolist())

# min sustained growth to keep debt < 90 (market) by 2029 given programmed pb
def min_growth_below90():
    r_base=base_real_r()
    for g2 in np.arange(-2,5,0.05):
        gp=dict(C.G)
        for y in (2028,2029): gp[y]=g2
        b=evolve(gp,r_base,C.PB,b0=C.B0_MARKET)     # market valuation vs the 90 line
        if b[2029]<90.0: return round(float(g2),2)
    return None

# ---------- from what year does the baseline need a primary SURPLUS? (pb* > 0) ----------
def surplus_year():
    p,de,sfa_cl,_=C.scen("S0"); rec=C.run(p,de_override=de,sfa_cl=sfa_cl)
    return [(r["year"], round(r["pb_star"],2), r["pb"]) for r in rec]

# ---------- sensitivity panels ----------
def sensitivity():
    r_base=base_real_r(); res={}
    # post-2028 growth
    res["growth_post2028"]={}
    for g2 in (0.0,1.0,2.0,2.75,3.5):
        gp=dict(C.G); [gp.__setitem__(y,g2) for y in range(2028,2036)]
        b=evolve(gp,r_base,C.PB); bm=evolve(gp,r_base,C.PB,b0=C.B0_MARKET)
        res["growth_post2028"][g2]=dict(b2029_off=round(b[2029],1),b2029_mkt=round(bm[2029],1),b2035_off=round(b[2035],1))
    # FX share x depreciation (sfa_FX channel): apply a 2027 second deprec of size d
    res["fx_deprec2027"]={}
    for d in (0.0,0.10,0.175,0.25):
        de2=dict(C.DE_OFFICIAL); de2[2027]=d
        for fx in (0.31,0.40):
            b=evolve(C.G,r_base,C.PB,de=de2,fx=fx)
            res["fx_deprec2027"][f"d={d},fx={fx}"]=round(b[2029],1)
    # contingent-liability size
    res["cl_size"]={}
    for cl in (0,5,7.5,10):
        s={y:0 for y in C.YEARS}; s[2027]=cl*0.55; s[2028]=cl*0.45
        b=evolve(C.G,r_base,C.PB,sfa_cl=s); res["cl_size"][cl]=round(b[2029],1)
    return res

def main():
    out={}
    out["fan_S0"]=fan("S0"); out["fan_S7"]=fan("S7")
    out["bifurcation"]=bifurcation()
    out["min_growth_below90_market"]=min_growth_below90()
    out["pb_star_by_year_S0"]=surplus_year()
    out["sensitivity"]=sensitivity()
    json.dump(out, open(os.path.join(OUT,"data","analysis.json"),"w"), indent=1, default=float)
    print("P(debt declining in 2029) : S0 = %.1f%% | S7 = %.1f%%"%(100*out["fan_S0"]["p_declining_2029"],100*out["fan_S7"]["p_declining_2029"]))
    print("S0 fan median debt path:", [round(x,1) for x in out["fan_S0"]["pct"][50]])
    print("S0 fan 90th pct        :", [round(x,1) for x in out["fan_S0"]["pct"][90]])
    print("min sustained growth to keep <90%% (market) by 2029:", out["min_growth_below90_market"], "%")
    print("\npb* (stabilizing primary, official) vs programmed pb, by year:")
    for y,pbs,pb in out["pb_star_by_year_S0"]:
        flag=" <-- needs SURPLUS" if pbs>0 and pb<=0 else ""
        print(f"  {y}: pb*={pbs:+.2f}  programmed={pb:+.1f}  gap={pbs-pb:+.2f}{flag}")
    print("\nsensitivity growth_post2028 (b2029 official / market):")
    for g2,v in out["sensitivity"]["growth_post2028"].items():
        print(f"  g={g2}: off={v['b2029_off']} mkt={v['b2029_mkt']} 2035off={v['b2035_off']}")
    return out

if __name__=="__main__": main()
