import numpy as np, geopandas as gpd, rasterio, pandas as pd, pyflwdir, json
from affine import Affine
from scipy.ndimage import minimum_filter
from shapely.geometry import LineString, Point
g=json.load(open('grid20.json')); tr=Affine(*g['tr'])
flw=pyflwdir.from_array(np.load('fdir20.npy'),ftype='d8',transform=tr,latlon=False)
upa=flw.upstream_area('m2')/43560  # acres
np.save('upa20_ac.npy',upa.astype('float32'))
feats=flw.streams(mask=upa>=8, uparea=upa)
st=gpd.GeoDataFrame.from_features(feats,crs=2272)
dom=gpd.read_file('domain.geojson').to_crs(2272).geometry.iloc[0]
rivpoly=gpd.read_file('nhd_area.geojson').to_crs(2272).buffer(30).union_all()
st=st[st.within(dom.buffer(-50))|st.intersects(dom.buffer(-50))]
st['geometry']=st.geometry.difference(rivpoly)
st=st.explode(index_parts=False); st=st[st.length>40]
print('stream segs',len(st))
ds=rasterio.open('dem3ft_ch.tif'); A=ds.read(1); H,W=A.shape
Amin=minimum_filter(np.where(A<-9000,1e4,A),size=5); del A
roads=pd.concat([gpd.read_file(f'tiger_{n}.geojson').to_crs(2272).assign(kind=n) for n in ['primary','secondary','local','rail']],ignore_index=True)
rn=roads.get('NAME',roads.get('FULLNAME'))
roads['rname']=roads['NAME'] if 'NAME' in roads else roads.iloc[:,0]
rsi=roads.sindex
step=4.0; recs=[]
def zs(pts):
    out=[]
    for p in pts:
        r,c=ds.index(p.x,p.y)
        out.append(Amin[r,c] if 0<=r<H and 0<=c<W and Amin[r,c]<1e4 else np.nan)
    return np.array(out)
for g_ in st.geometry:
    if g_.geom_type!='LineString': continue
    n=int(g_.length/step)+1
    if n<8: continue
    d=np.linspace(0,g_.length,n); pts=[g_.interpolate(t) for t in d]
    z=zs(pts)
    if np.isnan(z).mean()>0.2: continue
    z=pd.Series(z).interpolate(limit_direction='both').values
    zc=np.minimum.accumulate(z); blocked=(z-zc)>1.0
    i=0
    while i<n:
        if not blocked[i]: i+=1; continue
        s=i
        while i<n and blocked[i]: i+=1
        e=min(i,n-1); s0=max(s-1,0)
        crest=z[s:e+1].max(); k=max(1,int(30/step))
        zus=np.median(z[max(0,s0-k):s0+1]); zds=np.median(z[e:min(n,e+k)])
        relief=crest-max(zus,zds); L=d[e]-d[s0]
        if relief>=3.0 and L>=12:
            p_up=pts[s0]; p_dn=pts[e]; pc=pts[s+int(np.argmax(z[s:e+1]))]
            rr,cc=~tr*(p_up.x,p_up.y); rr,cc=int(cc),int(rr)
            da=float(upa[max(rr-2,0):rr+3,max(cc-2,0):cc+3].max())
            seg=LineString([(q.x,q.y) for q in pts[s0:e+1]])
            hit=list(rsi.query(seg.buffer(30)))
            recs.append(dict(us_inv=float(zc[s0]),ds_inv=float(min(z[e],zc[s0])),crest=float(crest),relief=float(relief),length=float(L),da_ac=da,
              road=(roads.iloc[hit[0]].rname if hit else None),kind=(roads.iloc[hit[0]].kind if hit else None),
              us_x=p_up.x,us_y=p_up.y,ds_x=p_dn.x,ds_y=p_dn.y,cx=pc.x,cy=pc.y,geometry=seg))
c=gpd.GeoDataFrame(recs,crs=2272); print(len(c)); print(c.kind.value_counts(dropna=False))
c.to_file('culvert_candidates_raw.gpkg')
