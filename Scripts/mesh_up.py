import numpy as np, geopandas as gpd, shapely, pandas as pd
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import linemerge, substring
from scipy.spatial import cKDTree
dom=gpd.read_file('domain.geojson').to_crs(2272).geometry.iloc[0]
per=Polygon(dom.exterior).simplify(15)
fl=gpd.read_file('nhd_flow0.geojson').to_crs(2272)
def river(n):
    L=linemerge(fl[fl.gnis_name==n].geometry.union_all().intersection(per.buffer(2000)))
    return max(L.geoms,key=lambda g:g.length) if L.geom_type=='MultiLineString' else L
S=river('Schuylkill River'); Pk=river('Perkiomen Creek')
ch=gpd.read_file('nhd_area.geojson').to_crs(2272); ch=ch[ch.FTYPE==460].geometry.union_all().intersection(per)
fz=gpd.read_file('fema_zones.geojson').to_crs(2272); fz['geometry']=fz.geometry.make_valid().buffer(0)
fp=fz[fz.FLD_ZONE.isin(['AE','A'])|(fz.ZONE_SUBTY.astype(str).str.contains('0.2'))].geometry.union_all().buffer(100).intersection(per)
# --- BC lines: perimeter pieces where rivers cross it
ext=per.exterior; bcs={}
for name,L in [('Schuylkill',S),('Perkiomen',Pk)]:
    X=L.intersection(ext); pts=[X] if X.geom_type=='Point' else list(X.geoms)
    for p in pts:
        d=L.project(p); end='US' if d<L.length/2 else 'DS'
        # flow direction: NHD digitized downstream -> start is upstream
        seg=ext.intersection(fp.buffer(50))
        segs=[g for g in getattr(seg,'geoms',[seg]) if g.distance(p)<1]
        if not segs: continue
        s=linemerge(segs[0]) if segs[0].geom_type=='MultiLineString' else segs[0]
        bcs[f'{name} {end}']=s
from shapely.ops import split
p=S.interpolate(S.project(Point(2606000,292000))); d=S.project(p)
q1=S.interpolate(d-200); q2=S.interpolate(d+200); dx,dy=q2.x-q1.x,q2.y-q1.y; L_=np.hypot(dx,dy); nx,ny=-dy/L_,dx/L_
cut=LineString([(p.x-nx*4000,p.y-ny*4000),(p.x+nx*4000,p.y+ny*4000)])
parts=sorted(split(per,cut).geoms,key=lambda g:-g.area); print('cut parts',[round(g.area/27878400,3) for g in parts])
per=Polygon(parts[0].exterior).simplify(5); ext=per.exterior
seg=ext.intersection(cut.buffer(2)); segs=list(getattr(seg,'geoms',[seg])); bds=max(segs,key=lambda g:g.length)
bcs['Schuylkill DS']=LineString([bds.coords[0],bds.coords[-1]])
fp=fp.intersection(per); ch=ch.intersection(per)
rs=gpd.read_file('river_sections.geojson').to_crs(2272).set_index('name').geometry
for nm,key in [('Perkiomen Creek','Perkiomen US'),('Schuylkill River','Schuylkill US')]:
    sec=rs[nm]; p0=Point(sec.coords[0]); p1=sec.interpolate(1.0)
    dx,dy=p1.x-p0.x,p1.y-p0.y; L_=np.hypot(dx,dy); nx,ny=-dy/L_,dx/L_
    capl=LineString([(p0.x-nx*3500,p0.y-ny*3500),(p0.x+nx*3500,p0.y+ny*3500)])
    fullL=S if nm=='Schuylkill River' else Pk
    d0=fullL.project(p0); up_=substring(fullL,max(d0-6000,0),d0)
    cutp=up_.buffer(500,cap_style=2).difference(capl.buffer(0.01).buffer(0))
    # keep only the part strictly upstream of cap: polygon side test
    side=lambda q:(q.x-p0.x)*dx+(q.y-p0.y)*dy
    rect=Polygon([(p0.x-nx*3500,p0.y-ny*3500),(p0.x+nx*3500,p0.y+ny*3500),(p0.x+nx*3500-dx/L_*8000,p0.y+ny*3500-dy/L_*8000),(p0.x-nx*3500-dx/L_*8000,p0.y-ny*3500-dy/L_*8000)])
    per=per.difference(up_.buffer(500).intersection(rect)); 
    if per.geom_type=='MultiPolygon': per=max(per.geoms,key=lambda g:g.area)
    per=Polygon(per.exterior); ext=per.exterior
    seg=ext.intersection(capl.buffer(3)); segs=[g for g in getattr(seg,'geoms',[seg]) if g.length>20]
    if segs:
        g=max(segs,key=lambda g:g.length); bcs[key]=LineString([g.coords[0],g.coords[-1]]) if g.geom_type=='LineString' else g
fp=fp.intersection(per); ch=ch.intersection(per)
for k,v in bcs.items(): print(k,round(v.length),v.geom_type)
# --- points
def grid(sp,zone,x0,y0,x1,y1,off=0.5):
    xs=np.arange(np.floor(x0/sp)*sp+sp*off,x1,sp); ys=np.arange(np.floor(y0/sp)*sp+sp*off,y1,sp)
    X,Y=np.meshgrid(xs,ys); P=np.c_[X.ravel(),Y.ravel()]
    return P[shapely.contains_xy(zone,P[:,0],P[:,1])]
x0,y0,x1,y1=per.bounds
C,F,B=40.0,60.0,100.0
banks=ch.boundary.intersection(per.buffer(-C))
fpz=fp.difference(ch.buffer(C*0.5))
upl=per.buffer(-0.5*B).difference(fp.buffer(B*0.3))
P1=grid(B,upl,x0,y0,x1,y1); P2=grid(F,fpz.buffer(-F*0.3).difference(ch.buffer(C)),x0,y0,x1,y1); P3=grid(C,ch.buffer(-C*0.75),x0,y0,x1,y1)
# bank-aligned pairs
bp=[]
for g in getattr(banks,'geoms',[banks]):
    if g.length<C: continue
    n=int(g.length/C)
    for t in (np.arange(n)+0.5)/n*g.length:
        p=g.interpolate(t); q=g.interpolate(min(t+1,g.length)); r_=g.interpolate(max(t-1,0))
        dx,dy=q.x-r_.x,q.y-r_.y; L_=np.hypot(dx,dy) or 1; nx,ny=-dy/L_,dx/L_
        bp+=[(p.x+nx*C/2,p.y+ny*C/2),(p.x-nx*C/2,p.y-ny*C/2)]
bp=np.array(bp)
P=np.vstack([P1,P2,P3]); P=P[shapely.distance(shapely.points(P[:,0],P[:,1]),banks)>C*0.8]
P=np.vstack([P,bp]); P=P[shapely.contains_xy(per.buffer(-C*0.5),P[:,0],P[:,1])]
t=cKDTree(P); pr=t.query_pairs(r=C*0.4); drop={max(i,j) for i,j in pr}; P=np.delete(P,list(drop),axis=0)
print('points',len(P),'upland',len(P1),'fp',len(P2),'chan',len(P3),'bank',len(bp))
np.save('mesh_points_up.npy',P)
gpd.GeoDataFrame({'name':['UpperProv']},geometry=[per],crs=2272).to_file('perimeter_up.gpkg')
gpd.GeoDataFrame({'name':list(bcs)},geometry=list(bcs.values()),crs=2272).to_file('bclines_up.gpkg')
gpd.GeoDataFrame(geometry=[ch],crs=2272).to_file('channel_up.gpkg'); gpd.GeoDataFrame(geometry=[fp],crs=2272).to_file('fpzone_up.gpkg')
