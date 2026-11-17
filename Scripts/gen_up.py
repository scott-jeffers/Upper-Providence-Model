import numpy as np, geopandas as gpd, json, os
P=os.environ.get("PDIR","proj/UpperProvidence/"); NAME="UpperProvidence"; SAn="UpperProv"; SA=f"{SAn:<16}"
per=gpd.read_file("perimeter_up.gpkg").geometry.iloc[0]
bcs=gpd.read_file("bclines_up.gpkg")
pts=np.load("mesh_points_up.npy")
def pairs(coords,per_line):
    vals=[v for xy in coords for v in xy]; out=[]
    for i in range(0,len(vals),per_line): out.append("".join(f"{v:>16.6f}"[-16:] if len(f'{v:.6f}')<=16 else f"{v:16.4f}" for v in vals[i:i+per_line]))
    return out
x0,y0,x1,y1=per.bounds
L=["Geom Title=Upper Providence 2D (Schuylkill+Perkiomen, lidar culverts burned)","Program Version=6.70",
   f"Viewing Rectangle= {x0:.2f} , {x1:.2f} , {y1:.2f} , {y0:.2f} ",""]
c=per.centroid
L.append(f"Storage Area={SA},{c.x:.4f},{c.y:.4f}")
pc=list(per.exterior.coords)
L.append(f"Storage Area Surface Line= {len(pc)} "); L+=pairs([(p[0],p[1]) for p in pc],2)
L+=["Storage Area Type= 1 ","Storage Area Area=","Storage Area Min Elev=","Storage Area Is2D=-1","Storage Area Point Generation Data=,,100,100"]
L.append(f"Storage Area 2D Points= {len(pts)} "); L+=pairs([tuple(p) for p in pts],4)
L+=["Storage Area 2D PointsPerimeterTime=16Nov2026 12:00:00","Storage Area Mannings=0.06",
"2D Cell Volume Filter Tolerance=0.01","2D Cell Minimum Area Fraction=0.01","2D Face Profile Filter Tolerance=0.01",
"2D Face Area Elevation Profile Filter Tolerance=0.01","2D Face Area Elevation Conveyance Ratio=0.02","2D Face Min Length Ratio=0.05",
"2D Face Area Laminar Depth=0.2","2D Multiple Face Mann n=0","2D Composite LC=0",""]
for r in bcs.itertuples():
    bcc=list(r.geometry.coords); m=r.geometry.interpolate(0.5,normalized=True)
    L+=[f"BC Line Name={r.name:<32}",f"BC Line Storage Area={SA}",
        f"BC Line Start Position= {bcc[0][0]} , {bcc[0][1]} ",f"BC Line Middle Position= {m.x} , {m.y} ",f"BC Line End Position= {bcc[-1][0]} , {bcc[-1][1]} ",
        f"BC Line Arc= {len(bcc)} "]
    L+=pairs(bcc,4); L+=["BC Line Text Position= 1.79769313486232E+308 , 1.79769313486232E+308 "]
L+=["LCMann Time=Dec/30/1899 00:00:00","LCMann Region Time=Dec/30/1899 00:00:00","LCMann Table=0","Chan Stop Cuts=-1 ","","","",
"Use User Specified Reach Order=0","GIS Ratio Cuts To Invert=-1","GIS Limit At Bridges=0","Composite Channel Slope=5",""]
if os.environ.get("WRITE_G"): open(P+NAME+".g01","w",newline="\r\n").write("\n".join(L)); print("g01 lines",len(L))
# ---------- scenarios
sc=json.load(open("scenarios_up.json"))
u=open("tpl_vc.u01").read().splitlines()
ia=[i for i,s in enumerate(u) if s.startswith("Boundary Location=")]
tail_start=[i for i,s in enumerate(u) if s.startswith("DSS Path=")][-1]   # after precip block
common=u[tail_start:]
p=open("tpl_vc.p01").read().splitlines()
def fmt8(v): s=f"{v:8.0f}"; return s
plans=[]
for k,s in enumerate(sc,1):
    hrs=s['hours']; qS=s['qS']; qP=s['qP']
    out=["Flow Title="+s['title'],"Program Version=6.60","Use Restart= 0 "]
    def flowbc(name,q,slope):
        b=[f"Boundary Location={'':16},{'':16},{'':8},{'':8},{'':16},{SA},{'':16},{name:<32},{'':32}","Interval=1HOUR",f"Flow Hydrograph= {len(q)} "]
        for i in range(0,len(q),10): b.append("".join(fmt8(v) for v in q[i:i+10]))
        b+=["Stage Hydrograph TW Check=0",f"Flow Hydrograph Slope= {slope} ","DSS Path=","Use DSS=False","Use Fixed Start Time=False","Fixed Start Date/Time=,","Is Critical Boundary=False","Critical Boundary Flow="]
        return b
    out+=flowbc("Schuylkill US",qS,0.0005)+flowbc("Perkiomen US",qP,0.001)
    R=json.load(open('ds_rating.json')); qt=[a+b for a,b in zip(qS,qP)]; qt=[qt[0]]+qt[:-1]
    stg=[float(np.interp(q,R['q'],R['h'])) for q in qt]
    out+=[f"Boundary Location={'':16},{'':16},{'':8},{'':8},{'':16},{SA},{'':16},{'Schuylkill DS':<32},{'':32}","Interval=1HOUR",f"Stage Hydrograph= {len(stg)} "]
    for i in range(0,len(stg),10): out.append("".join(f"{v:8.2f}" for v in stg[i:i+10]))
    out+=["DSS Path=","Use DSS=False","Use Fixed Start Time=False","Fixed Start Date/Time=,","Is Critical Boundary=False","Critical Boundary Flow="]
    out+=common
    open(P+f"{NAME}.u{k:02d}","w",newline="\r\n").write("\n".join(out)+"\n")
    q=[]
    for line in p:
        t=line
        if t.startswith("Plan Title="): t="Plan Title="+s['title']
        elif t.startswith("Short Identifier="): t="Short Identifier="+s['short']
        elif t.startswith("Simulation Date="): t=f"Simulation Date=01JAN2026,0000,01JAN2026,{hrs-1:02d}00" if hrs<=24 else "Simulation Date=01JAN2026,0000,02JAN2026,0000"
        elif t.startswith("Geom File="): t="Geom File=g01"
        elif t.startswith("Flow File="): t=f"Flow File=u{k:02d}"
        elif t.startswith("Computation Interval="): t="Computation Interval=10SEC"
        elif t.startswith("Output Interval="): t="Output Interval=15MIN"
        elif t.startswith("Mapping Interval="): t="Mapping Interval=30MIN"
        elif t.startswith("Computation Time Step Max Courant="): t="Computation Time Step Max Courant=3"
        elif t.startswith("Computation Time Step Min Courant="): t="Computation Time Step Min Courant=1"
        elif t.startswith("Computation Time Step Max Doubling="): t="Computation Time Step Max Doubling=2"
        elif t.startswith("UNET D2 Name="): t=f"UNET D2 Name={SA}"
        elif t.startswith("UNET D2 Z Tol="): t="UNET D2 Z Tol= 0.02 "
        q.append(t)
    plans.append(k)
    if os.environ.get("WRITE_P"): open(P+f"{NAME}.p{k:02d}","w",newline="\r\n").write("\n".join(q)+"\n")
pj=open("tpl.prj").read().replace("Proj Title=DavisStormSystem","Proj Title=Upper Providence Twp (Montgomery Co PA) 2D").replace("Current Plan=p02","Current Plan=p01")
pj=pj.replace("Geom File=g02","Geom File=g01")
import re
pj=re.sub(r"Unsteady File=u\d+\n","",pj.replace("\r\n","\n")); pj=re.sub(r"Plan File=p\d+\n","",pj)
pj=pj.replace("Geom File=g01\n","Geom File=g01\n"+"".join(f"Unsteady File=u{k:02d}\n" for k in plans)+"".join(f"Plan File=p{k:02d}\n" for k in plans))
if os.environ.get("WRITE_P"): open(P+NAME+".prj","w",newline="\r\n").write(pj)
print(len(plans),"plans")
