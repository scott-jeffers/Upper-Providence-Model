import numpy as np, geopandas as gpd, rasterio, pandas as pd, math, json, shapely
from shapely.geometry import LineString
from rasterio.windows import from_bounds
pd.set_option('display.width',250)
A14=json.load(open('atlas14.json'))
dur=np.array([5,10,15,30,60,120,180]); dep=np.array([A14[k]['10'] for k in ['5min','10min','15min','30min','60min','2hr','3hr']])
def i10(tc): return math.exp(np.interp(math.log(tc),np.log(dur),np.log(dep/(dur/60))))
def Q10(da):
    def qr(a): tc=10+25*math.sqrt(a/640); return 0.39*i10(tc)*a
    return qr(da) if da<=200 else qr(200)*(da/200)**0.6
g=gpd.read_file('culvert_candidates.gpkg').reset_index(drop=True)
nbi=gpd.read_file('nbi.geojson').to_crs(2272); nbi=nbi[nbi.SERVICE_UND_042B.astype(str).isin(['5','6','7','8','9'])]
pipes=[1.25,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6]; cap=lambda D: 2.36*D**2.5
recs=[]
for i,r in g.iterrows():
    q=Q10(r.da_ac); seg=r.geometry
    dn=nbi.distance(seg); j=dn.idxmin() if len(dn) else None
    us=r.us_inv; ds_=r.ds_inv
    if ds_>=us-0.05: ds_=us-max(0.005*r.length,0.1)
    hgt=r.crest-us; maxrise=max(1.25,min(hgt-1.0,12))
    typ='pipe'; rise=None; span=0; nb=1; nbi_id=None
    if j is not None and dn[j]<150:
        b=min(150,max(10,float(nbi.loc[j,'STRUCTURE_LEN_MT_049'])*3.28084*0.85)); typ='bridge(NBI)'; nbi_id=nbi.loc[j,'STRUCTURE_NUMBER_008']; rise=hgt
    elif r.da_ac>=640:
        b=max(10,12*math.sqrt(r.da_ac/640)); typ='bridge/box(est)'; rise=min(hgt,10)
    else:
        for D in pipes:
            if D<=maxrise and cap(D)>=q: rise=D; break
        if rise is None:
            D=max([p for p in pipes if p<=maxrise] or [1.25]); nb=math.ceil(q/cap(D))
            if nb<=3 and r.da_ac<=500: rise=D
            else:
                typ='box'; rise=max(2,min(math.floor(maxrise),10)); B=q/(3.3*rise**1.5); nb=max(1,math.ceil(B/16)); span=min(16,max(3,math.ceil(B/nb)))
        b=max(3.0,nb*(span if typ=='box' else rise)+max(0,nb-1)*1.0); b=min(b,max(8,15*math.sqrt(r.da_ac/640)))
    recs.append(dict(cid=f'U{i+1:03d}',type=typ,rise_ft=round(rise,1),span_ft=span,barrels=nb,notch_w_ft=round(b,1),length_ft=round(max(r.length,20),0),
        us_inv=round(us,2),ds_inv=round(ds_,2),crest=round(r.crest,2),q10_cfs=round(q,1),da_ac=round(r.da_ac,1),road=r.road,kind=r.kind,nbi=nbi_id,geometry=seg))
c=gpd.GeoDataFrame(recs,crs=2272)
drop=c[(c.length_ft>300)&(c['type']!='bridge(NBI)')]; print('dropped long',len(drop)); drop.to_file('culverts_up_dropped_long.gpkg')
c=c.drop(index=drop.index).reset_index(drop=True); c['cid']=[f'U{i+1:03d}' for i in range(len(c))]
print(c.type.value_counts()); print(c[c.type!='pipe'][['cid','type','notch_w_ft','length_ft','da_ac','road','nbi']].to_string())
c.to_file('culverts_up.gpkg'); c.drop(columns='geometry').assign(x=c.geometry.centroid.x,y=c.geometry.centroid.y).to_csv('culverts_up.csv',index=False)
# burn
src=rasterio.open('dem3ft_ch.tif'); A=src.read(1); T=src.transform
for _,r in c.iterrows():
    co=list(r.geometry.coords)
    if len(co)<2: continue
    p0=np.array(co[0]); p1=np.array(co[-1])
    u0=p0-np.array(co[1]); u0/=np.linalg.norm(u0)+1e-9; u1=p1-np.array(co[-2]); u1/=np.linalg.norm(u1)+1e-9
    line=LineString([tuple(p0+u0*10)]+co+[tuple(p1+u1*10)]); b=r.notch_w_ft
    win=from_bounds(*line.buffer(b/2+15).bounds,T).round_offsets().round_lengths()
    r0,c0=int(win.row_off),int(win.col_off); h,w=int(win.height),int(win.width)
    sub=A[r0:r0+h,c0:c0+w]; rows,cols=np.indices(sub.shape)
    P=shapely.points(T.c+(c0+cols.ravel()+0.5)*T.a, T.f+(r0+rows.ravel()+0.5)*T.e)
    dd=shapely.distance(P,line).reshape(sub.shape); tt=(shapely.line_locate_point(line,P)/line.length).reshape(sub.shape)
    prof=r.us_inv+(r.ds_inv-r.us_inv)*tt; newz=np.where(dd<=b/2,prof,prof+(dd-b/2)*1.0)
    m=(dd<=b/2+15)&(sub>-9000); sub[m]=np.minimum(sub[m],newz[m]).astype(np.float32); A[r0:r0+h,c0:c0+w]=sub
with rasterio.open('dem3ft_hydro.tif','w',**src.profile) as o: o.write(A,1)
print('burned',len(c))
