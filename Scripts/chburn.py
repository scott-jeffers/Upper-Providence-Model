import rasterio,numpy as np,geopandas as gpd,os,time
from rasterio.features import rasterize
from rasterio.windows import Window
from scipy import ndimage
riv=gpd.read_file('nhd_area.geojson').to_crs(2272); riv=riv[riv.FTYPE.isin([460,336])]
src=rasterio.open('dem3ft.tif'); H,W=src.shape; res=src.res[0]
prof=src.profile
st=int(open('chburn.state').read()) if os.path.exists('chburn.state') else 0
if st==0: rasterio.open('dem3ft_ch.tif','w',**prof).close()
o=rasterio.open('dem3ft_ch.tif','r+')
B=2048;OV=250;t0=time.time();tiles=[(r,c) for r in range(0,H,B) for c in range(0,W,B)]
stats=[]
for k in range(st,len(tiles)):
    if time.time()-t0>130: print('PAUSE',k); break
    r,c=tiles[k]
    r0,c0=max(0,r-OV),max(0,c-OV); r1,c1=min(H,r+B+OV),min(W,c+B+OV)
    win=Window(c0,r0,c1-c0,r1-r0); a=src.read(1,window=win)
    wt=src.window_transform(win)
    m=rasterize(((g,1) for g in riv.geometry),out_shape=a.shape,transform=wt,fill=0,dtype='uint8').astype(bool)&(a>-9000)
    if m.any():
        dist=ndimage.distance_transform_edt(m)*res
        hw=ndimage.maximum_filter(dist,size=121)  # ~400 ft window
        hw=ndimage.grey_dilation(hw,size=1)
        dmax=np.clip(hw/20.0,0.5,7.0)
        dep=np.where(m,dmax*np.minimum(1.0,dist/np.maximum(0.35*hw,1)),0)
        a=np.where(m,a-dep,a).astype('float32'); stats.append(float(dep.max()))
    ir,ic=r-r0,c-c0; h=min(B,H-r); w=min(B,W-c)
    o.write(a[ir:ir+h,ic:ic+w],1,window=Window(c,r,w,h))
    open('chburn.state','w').write(str(k+1))
print('done to',k+1,len(tiles),'maxdep',max(stats) if stats else 0)
