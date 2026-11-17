import h5py, numpy as np, rasterio, geopandas as gpd, pandas as pd, os
from rasterio.features import rasterize
from rasterio.enums import Resampling
from rasterio.warp import reproject
from shapely.geometry import Polygon
P=os.path.expanduser('~/mnt/Upper-Providence-Model/Model/UpperProvidence/')
f=h5py.File(P+'UpperProvidence.g01.hdf','r'); A='Geometry/2D Flow Areas/UpperProv/'
fpi=f[A+'Cells FacePoint Indexes'][:]; fpc=f[A+'FacePoints Coordinate'][:]; per=f[A+'Perimeter'][:]
x0,y0=per.min(0)-50; x1,y1=per.max(0)+50; R=10.0
W=int((x1-x0)/R); H=int((y1-y0)/R); tr=rasterio.transform.from_origin(x0,y1,R,R)
shapes=[]
for i,row in enumerate(fpi):
    idx=row[row>=0]
    if len(idx)>=3: shapes.append((Polygon(fpc[idx]).buffer(0),i))
cell=rasterize(shapes,out_shape=(H,W),transform=tr,fill=-1,dtype='int32')
dem=rasterio.open(P+'Terrain/UP_DEM_1m_ft_hydro.tif'); d=np.full((H,W),np.nan,'float32')
reproject(rasterio.band(dem,1),d,dst_transform=tr,dst_crs=dem.crs,resampling=Resampling.average,dst_nodata=np.nan,src_nodata=-9999)
np.savez_compressed('static.npz',cell=cell,dem=d,x0=x0,y1=y1,R=R); print(W,H,(cell>=0).mean())
U=os.path.expanduser('~/up/')
rd=pd.concat([gpd.read_file(U+f'tiger_{n}.geojson').to_crs(2272).assign(kind=n) for n in ['primary','secondary','local']],ignore_index=True)
nm=[c for c in rd.columns if c.upper() in ('NAME','FULLNAME','BASENAME')]; rd['name']=rd[nm[0]] if nm else ''
dom=Polygon(per); rd=rd[rd.intersects(dom)][['name','kind','geometry']]; rd.to_file('roads.gpkg'); print('roads',len(rd))
b=gpd.read_file(U+'buildings.geojson').to_crs(2272); b=b[b.intersects(dom)].reset_index(drop=True); b['bid']=['B%05d'%i for i in range(len(b))]; b.to_file('buildings.gpkg'); print('bldg',len(b))
