import rasterio, numpy as np, glob, os
from rasterio.warp import reproject, Resampling, transform_bounds
from rasterio.transform import from_origin
src=sorted(glob.glob(os.path.expanduser('~/mnt/Upper-Providence-Model/Terrain/raw/*.tif')))
b=[rasterio.open(f).bounds for f in src]
w,s,e,n=min(x.left for x in b),min(x.bottom for x in b),max(x.right for x in b),max(x.top for x in b)
W,S,E,N=transform_bounds(26918,2272,w,s,e,n)
R=10.0; W=np.floor(W/R)*R; N=np.ceil(N/R)*R
nx=int((E-W)/R); ny=int((N-S)/R); tr=from_origin(W,N,R,R)
out=np.full((ny,nx),np.nan,'float32')
for f in src:
    r=rasterio.open(f); tmp=np.full((ny,nx),np.nan,'float32')
    reproject(rasterio.band(r,1),tmp,dst_transform=tr,dst_crs='EPSG:2272',resampling=Resampling.average,dst_nodata=np.nan)
    m=np.isfinite(tmp)&~np.isfinite(out); out[m]=tmp[m]
out=out*3.28084  # m -> ft
prof=dict(driver='GTiff',height=ny,width=nx,count=1,dtype='float32',crs='EPSG:2272',transform=tr,nodata=np.nan,compress='deflate',tiled=True)
with rasterio.open('dem10ft.tif','w',**prof) as d: d.write(out,1)
print(nx,ny,np.nanmin(out),np.nanmax(out),np.isfinite(out).mean())
