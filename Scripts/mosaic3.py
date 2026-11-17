import rasterio, numpy as np, geopandas as gpd, glob, sys
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from rasterio.merge import merge
from rasterio.windows import Window
from rasterio.transform import from_origin
d=gpd.read_file('domain.geojson').to_crs(2272); x0,y0,x1,y1=d.buffer(500).total_bounds
res=3.28084; x0=np.floor(x0/10)*10; y1=np.ceil(y1/10)*10
W=int(np.ceil((x1-x0)/res)); H=int(np.ceil((y1-y0)/res)); tr=from_origin(x0,y1,res,res)
print(W,H,W*H/1e6)
M='/sessions/rcw-01cegc68wre92zsojpactfts/mnt/Upper-Providence-Model/Terrain/raw/'
srcs=[rasterio.open(f) for f in sorted(glob.glob(M+'*.tif'))]
vrts=[WarpedVRT(s,crs='EPSG:2272',transform=tr,width=W,height=H,resampling=Resampling.bilinear,src_nodata=s.nodata,nodata=-9999) for s in srcs]
prof=dict(driver='GTiff',width=W,height=H,count=1,dtype='float32',crs='EPSG:2272',transform=tr,nodata=-9999,tiled=True,blockxsize=512,blockysize=512,compress='deflate',predictor=3,BIGTIFF='YES')
import os,time
t0=time.time()
st=int(open('mosaic3.state').read()) if os.path.exists('mosaic3.state') else 0
if st==0: rasterio.open('dem3ft.tif','w',**prof).close()
with rasterio.open('dem3ft.tif','r+') as o:
    B=1024
    for r in range(st,H,B):
        if time.time()-t0>120: print('PAUSE',r); break
        for c in range(0,W,B):
            w=Window(c,r,min(B,W-c),min(B,H-r)); out=np.full((w.height,w.width),-9999,'float32')
            for v in vrts:
                a=v.read(1,window=w)
                m=(a!=-9999)&(out==-9999)&(a>-1000); out[m]=a[m]*3.28084
            o.write(out,1,window=w)
        open('mosaic3.state','w').write(str(r+B)); print(r,flush=True)
