# -*- coding: utf-8 -*-
"""dsa_exhibits.py — emit tables (.tex + .md) and the fan figure from scenarios.json / analysis.json."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
OUT=os.path.join(os.path.dirname(__file__),".."); EX=os.path.join(OUT,"exhibits")
os.makedirs(EX,exist_ok=True)
S=json.load(open(os.path.join(OUT,"data","scenarios.json")))
A=json.load(open(os.path.join(OUT,"data","analysis.json")))
YEARS=list(range(2026,2036))
def rec(s): return {r["year"]:r for r in S[s]["rec"]}

# ---- tab_debt_paths: debt %GDP, official + market, all scenarios ----
def tab_debt_paths():
    lines=[r"\begin{tabular}{l"+"r"*6+"}",r"\hline",
           r"Debt \% GDP (official / market) & 2026 & 2027 & 2028 & 2029 & 2031 & 2035\\ \hline"]
    for s in ["S0","S1","S2","S3","S4","S5","S6","S7","S8"]:
        R=rec(s)
        off=" & ".join(f"{R[y]['b_off']:.0f}/{R[y]['b_mkt']:.0f}" for y in (2026,2027,2028,2029,2031,2035))
        lines.append(f"{s} ({S[s]['note'][:22]}) & {off}\\\\")
    lines+=[r"\hline",r"\end{tabular}"]
    open(os.path.join(EX,"tab_debt_paths.tex"),"w").write("\n".join(lines))
    # md mirror
    md=["| scenario | 2026 | 2027 | 2028 | 2029 | 2031 | 2035 |","|---|---|---|---|---|---|---|"]
    for s in ["S0","S1","S2","S3","S4","S5","S6","S7","S8"]:
        R=rec(s); md.append(f"| {s} {S[s]['note'][:20]} | "+" | ".join(f"{R[y]['b_off']:.0f}/{R[y]['b_mkt']:.0f}" for y in (2026,2027,2028,2029,2031,2035))+" |")
    open(os.path.join(EX,"tab_debt_paths.md"),"w").write("Debt %GDP, **official/market** valuation.\n\n"+"\n".join(md))

# ---- tab_rminusg: r-g, g*, pb* by year (S0) + r-g by scenario ----
def tab_rminusg():
    R=rec("S0")
    md=["r−g, stabilizing g*, stabilizing pb* vs programmed pb, **S0** (official valuation)","",
        "| year | r−g | g* (stabilizing) | pb* | programmed pb | pb gap |","|---|---|---|---|---|---|"]
    for y in YEARS:
        r=R[y]; md.append(f"| {y} | {r['rminusg']:+.1f} | {r['g_star']:+.1f} | {r['pb_star']:+.2f} | {r['pb']:+.1f} | {r['pb_star']-r['pb']:+.2f} |")
    md+=["","r−g by scenario:","","| scenario | 2026 | 2027 | 2028 | 2029 | 2031 |","|---|---|---|---|---|---|"]
    for s in ["S0","S1","S4","S5","S7"]:
        Rs=rec(s); md.append(f"| {s} | "+" | ".join(f"{Rs[y]['rminusg']:+.1f}" for y in (2026,2027,2028,2029,2031))+" |")
    open(os.path.join(EX,"tab_rminusg.md"),"w").write("\n".join(md))

# ---- tab_gfn ----
def tab_gfn():
    md=["Gross financing needs (%GDP) = amortization + interest + overall deficit, **S0**","",
        "| year | amort | interest | overall deficit | GFN | note |","|---|---|---|---|---|---|"]
    R=rec("S0")
    for y in YEARS:
        r=R[y]; note="liquidity peak" if y in (2026,2027) else ("solvency-favourable" if r['rminusg']<0 else "")
        md.append(f"| {y} | {r['amort']:.1f} | {r['interest']:.1f} | {r['overall_def']:.1f} | {r['gfn']:.1f} | {note} |")
    open(os.path.join(EX,"tab_gfn.md"),"w").write("\n".join(md))

# ---- DSA standard table (S0 + key stresses) ----
def dsa_table():
    md=["# DSA_TABLE: standard fan-chart table (S0 and key stresses)","",
        "Debt (official/market %GDP), GFN (%GDP), r−g, primary balance (%GDP), sfa_FX (pp).",""]
    for s in ["S0","S1","S6","S7"]:
        R=rec(s); md.append(f"## {s}: {S[s]['note']}")
        md.append("| year | debt off/mkt | GFN | r−g | pb | sfa_FX |")
        md.append("|---|---|---|---|---|---|")
        for y in YEARS:
            r=R[y]; md.append(f"| {y} | {r['b_off']:.0f}/{r['b_mkt']:.0f} | {r['gfn']:.1f} | {r['rminusg']:+.1f} | {r['pb']:+.1f} | {r['sfa_fx_off']:+.1f} |")
        md.append("")
    open(os.path.join(OUT,"outputs","DSA_TABLE.md"),"w").write("\n".join(md))

# ---- fig_debt_fan ----
def fig_fan():
    yrs=A["fan_S0"]["years"]; pct=A["fan_S0"]["pct"]
    fig,ax=plt.subplots(figsize=(7,4.2))
    ax.fill_between(yrs,pct["10"],pct["90"],alpha=.15,color="#3b6",label="S0 fan 10–90")
    ax.fill_between(yrs,pct["25"],pct["75"],alpha=.25,color="#3b6")
    ax.plot(yrs,pct["50"],color="#184",lw=2,label="S0 median")
    for s,c in [("S1","#c60"),("S7","#b22"),("S8","#26c")]:
        R=rec(s); ax.plot([2025]+YEARS,[80.0]+[R[y]["b_off"] for y in YEARS],c,lw=1.4,label=f"{s} {S[s]['note'][:16]}")
    ax.axhline(90,ls="--",color="#888",lw=1); ax.text(2034,90.4,"90% (MEFP line)",fontsize=8,color="#666")
    ax.set_ylabel("SPNF debt, % GDP (official valuation)"); ax.set_xlabel("")
    ax.set_title("Bolivia SPNF debt: MEFP baseline fan and stress paths",fontsize=10)
    ax.legend(fontsize=7,loc="upper right"); ax.grid(alpha=.25)
    fig.tight_layout(); fig.savefig(os.path.join(EX,"fig_debt_fan.png"),dpi=140); plt.close()

for f in (tab_debt_paths,tab_rminusg,tab_gfn,dsa_table,fig_fan): f()
print("exhibits written to", EX)
print("DSA_TABLE.md written to outputs/")
