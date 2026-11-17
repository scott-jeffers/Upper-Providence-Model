import rasterio, numpy as np, geopandas as gpd, pyflwdir
from rasterio.enums import Resampling
from rasterio.features import rasterize, shapes
from shapely.geometry import shape
r=rasterio.open('dem10ft.tif')
H,W=r.height//2, r.width//2
dem=r.read(1,out_shape=(H,W),resampling=Resampling.average).astype('float32')
tr=r.transform*r.transform.scale(r.width/W, r.height/H)
nod=~np.isfinite(dem); dem[nod]=-9999
T=gpd.read_file('township.geojson').to_crs(2272)
nhd=gpd.read_file('nhd_flow0.geojson').to_crs(2272)
riv=nhd[nhd.gnis_name.isin(['Schuylkill River','Perkiomen Creek'])]
loc=nhd[~nhd.gnis_name.isin(['Schuylkill River','Perkiomen Creek'])]
rmask=rasterize(((g.buffer(260 if n=='Schuylkill River' else 130),1) for g,n in zip(riv.geometry,riv.gnis_name)),out_shape=(H,W),transform=tr,fill=0,dtype='uint8')
smask=rasterize(((g.buffer(15),1) for g in loc.geometry),out_shape=(H,W),transform=tr,fill=0,dtype='uint8')
d=dem.copy(); d[(smask==1)&~nod]-=5; d[(rmask==1)&~nod]-=15
flw=pyflwdir.from_dem(d,nodata=-9999,transform=tr,latlon=False,outlets='min')
tm=rasterize(((g,1) for g in T.geometry),out_shape=(H,W),transform=tr,fill=0,dtype='uint8')
lab=np.zeros((H,W),'int32'); lab[(tm==1)&(rmask==0)]=1; lab[rmask==1]=2
idx=np.flatnonzero(lab.ravel()>0)
bas=flw.basins(idxs=idx,ids=lab.ravel()[idx].astype('int32'))
dom=((bas==1)|(tm==1)).astype('uint8')
geoms=[shape(g) for g,v in shapes(dom,mask=dom==1,transform=tr) if v==1]
g=gpd.GeoSeries(geoms,crs=2272); g=g[g.area==g.area.max()] if len(g) else g
up=g.union_all()
out=gpd.GeoDataFrame({'name':['local_drainage']},geometry=[up],crs=2272)
out.to_file('local_drainage.geojson')
print('township sqmi',round(T.area.sum()/27878400,2),'local drainage sqmi',round(up.area/27878400,2))
np.save('fdir20.npy',flw.to_array('d8')); 
import json; json.dump({'tr':list(tr)[:6],'H':H,'W':W},open('grid20.json','w'))
