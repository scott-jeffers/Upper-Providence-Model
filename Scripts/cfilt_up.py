import numpy as np, geopandas as gpd, rasterio, pyflwdir, pandas as pd, os
pd.set_option('display.width',250)
ds=rasterio.open('dem10ft.tif'); a=ds.read(1).astype(np.float32)
if not os.path.exists('filldepth10.npy'):
    fill=pyflwdir.dem.fill_depressions(a,nodata=-9999,outlets='edge')[0]; np.save('filldepth10.npy',(fill-a).astype('float32'))
fd=np.load('filldepth10.npy')
g=gpd.read_file('culvert_candidates_raw.gpkg'); g['da_ac']=g.da_ac/10.7639
fl=gpd.read_file('nhd_flow0.geojson').to_crs(2272); big=fl[fl.gnis_name.isin(['Schuylkill River','Perkiomen Creek'])].buffer(300).union_all().union(gpd.read_file('nhd_area.geojson').to_crs(2272).buffer(150).union_all())
g=g[~g.geometry.intersects(big)]
roads=pd.concat([gpd.read_file(f'tiger_{n}.geojson').to_crs(2272).assign(kind=n) for n in ['primary','secondary','local','rail']],ignore_index=True)
nm=[c for c in roads.columns if c.upper() in ('NAME','FULLNAME','BASENAME')]; roads['rname']=roads[nm[0]] if nm else None
j=gpd.sjoin(g[['geometry']].assign(i=range(len(g))),roads[['rname','kind','geometry']].assign(geometry=roads.buffer(40)),predicate='intersects',how='left')
pri={'primary':0,'secondary':1,'rail':2,'local':3}
j['p']=j.kind.map(pri).fillna(9); j=j.sort_values('p').drop_duplicates('i').sort_values('i')
g['road']=j.rname.values; g['kind']=j.kind.values
lu=gpd.read_file('lulc2023.geojson').to_crs(2272)
mine=lu[lu.lu23subn.astype(str).str.contains('Mining|Quarr|Extract',case=False,na=False)]
mine=mine.buffer(50).union_all() if len(mine) else None
def fdmax(x,y,r=3):
    rr,cc=ds.index(x,y); return float(fd[max(rr-r,0):rr+r+1,max(cc-r,0):cc+r+1].max())
g['pond_us']=[fdmax(x,y) for x,y in zip(g.us_x,g.us_y)]
g['in_quarry']=g.geometry.intersects(mine) if mine is not None else False
nhd=fl[fl.gnis_name.notna()].buffer(60).union_all()
g['on_named']=g.geometry.intersects(nhd)
road=g.kind.notna()
keep=(~g.in_quarry)&(g.da_ac>=5)&( (road&((g.da_ac<=1500)|g.on_named)) | ((~road)&(g.relief<10)&(g.length<=120)&(g.da_ac>=15)&(g.da_ac<=1500)) )
k=g[keep].sort_values('da_ac',ascending=False).copy()
sel=[];cent=[]
for i,r in k.iterrows():
    p=r.geometry.centroid
    if all(p.distance(q)>60 for q in cent): sel.append(i); cent.append(p)
k=k.loc[sel]
print('kept',len(k),'of',len(g)); print(k.kind.value_counts(dropna=False))
print(pd.cut(k.da_ac,[0,20,50,200,640,3000,1e6]).value_counts().sort_index())
print(k[['road','kind','relief','length','da_ac','pond_us']].head(30).round(1).to_string())
k.to_file('culvert_candidates.gpkg')
