# -*- coding: utf-8 -*-
"""v1_figures.py — fig_growth_crosscheck and fig_scenarios (S0/S9/S10/S6 overlay)."""
import json, os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
OUT=os.path.join(os.path.dirname(__file__),".."); EX=os.path.join(OUT,"exhibits")
R=json.load(open(os.path.join(OUT,"outputs","v1_scenarios.json")))
SLATE="#243b53"; ACCENT="#b5482f"; AMBER="#c9852b"; TEAL="#2a7f7f"; GREY="#8a97a5"

# ---- growth cross-check: three independent near-term reads ----
def fig_growth():
    fig,ax=plt.subplots(figsize=(6.6,2.9))
    # points: (label, value, lo, hi, color)  -- near-term 2025-26
    rows=[("MEFP program\n(2026, program-consistent)", -1.0, None, None, SLATE),
          ("MFMod-BOL v5\n(2025, independent)", -3.3, None, None, TEAL),
          ("ISAE / NO2 nowcast\n(Sep 2025 – Aug 2026)", -2.8, -6.0, -1.4, ACCENT)]
    for i,(lab,v,lo,hi,c) in enumerate(rows):
        y=len(rows)-i
        if lo is not None: ax.plot([lo,hi],[y,y],color=c,lw=2,alpha=.5,solid_capstyle="round")
        ax.scatter([v],[y],color=c,s=60,zorder=3)
        ax.text(v,y+0.18,f"{v:+.1f}",ha="center",fontsize=8,color=c)
        ax.text(-6.6,y,lab,ha="right",va="center",fontsize=7.5)
    ax.axvline(-1.0,ls=":",color=SLATE,lw=1)
    ax.set_xlim(-7.2,0.5); ax.set_ylim(0.4,3.8); ax.set_yticks([])
    ax.set_xlabel("real GDP growth, percent (near-term reads)",fontsize=8)
    ax.set_title("Independent near-term growth reads: the program is the optimistic outlier",fontsize=9)
    for s in ("top","right","left"): ax.spines[s].set_visible(False)
    ax.grid(axis="x",alpha=.25); fig.tight_layout()
    fig.savefig(os.path.join(EX,"fig_growth_crosscheck.png"),dpi=150); plt.close()

# ---- scenario overlay: official-valuation debt paths ----
def fig_scen():
    yrs=[2025,2026,2027,2028,2029,2030,2031,2032,2033,2034,2035]
    def path(key): return [80.0]+[R[key][str(y)][0] if str(y) in R[key] else R[key][y][0] for y in yrs[1:]]
    def path_m(key): return [90.0]+[R[key][str(y)][1] if str(y) in R[key] else R[key][y][1] for y in yrs[1:]]
    fig,ax=plt.subplots(figsize=(6.8,3.6))
    ax.plot(yrs,path("S0"),color=SLATE,lw=2,label="S0 MEFP baseline")
    ax.fill_between(yrs,path("S9_lower"),path("S9_upper"),color=ACCENT,alpha=.12)
    ax.plot(yrs,path("S9_central"),color=ACCENT,lw=1.6,label="S9 ISAE near-term (−2.8; band −6 to −1.4)")
    ax.plot(yrs,path("S10"),color=AMBER,lw=1.6,ls="--",label="S10 disinflation-repricing success")
    ax.plot(yrs,path("S6_central"),color=TEAL,lw=1.6,ls="-.",label="S6 contingent liabilities (7% GDP)")
    ax.axhline(90,ls="--",color=GREY,lw=1); ax.text(2034.1,90.4,"90% line",fontsize=7.5,color="#666")
    ax.set_ylabel("SPNF debt, % GDP (official valuation)",fontsize=8.5)
    ax.set_title("New scenarios against the MEFP baseline",fontsize=9.5)
    ax.legend(fontsize=7,loc="lower left"); ax.grid(alpha=.25)
    for s in ("top","right"): ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(os.path.join(EX,"fig_scenarios.png"),dpi=150); plt.close()

fig_growth(); fig_scen()
print("figures written:", os.listdir(EX))
