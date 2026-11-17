import h5py,numpy as np,geopandas as gpd,sys
from scipy.spatial import cKDTree
P=sys.argv[1]; M='/sessions/rcw-01cegc68wre92zsojpactfts/mnt/Upper-Providence-Model/Model/UpperProvidence/'
f=h5py.File(M+f'UpperProvidence.{P}.hdf','r')
g='Geometry/2D Flow Areas/UpperProv/'
cc=f[g+'Cells Center Coordinate'][:]; minel=f[g+'Cells Minimum Elevation'][:]
base='Results/Unsteady/Output/Output Blocks/Base Output/Summary Output/2D Flow Areas/UpperProv/'
mx=f[base+'Maximum Water Surface'][0]
ts='Results/Unsteady/Output/Output Blocks/Base Output/Unsteady Time Series/2D Flow Areas/UpperProv/Water Surface'
ws=f[ts]; print('timesteps',ws.shape)
n=min(len(cc),len(mx)); cc=cc[:n]; mx=mx[:n]; minel=minel[:n]
wet=(mx-minel)>0.05
t=cKDTree(cc[wet]); W=mx[wet]
xs=gpd.read_file('fema_xs.geojson').to_crs(2272)
rows=[]
for r in xs.itertuples():
    if r.WTR_NM not in ('SCHUYLKILL RIVER','PERKIOMEN CREEK'): continue
    pts=[r.geometry.interpolate(s,normalized=True) for s in np.linspace(0.3,0.7,9)]
    d,i=t.query([(p.x,p.y) for p in pts]); 
    if d.min()>150: continue
    rows.append((r.WTR_NM,r.STREAM_STN,r.WSEL_REG,float(np.median(W[i[d<150]]))))
import pandas as pd
df=pd.DataFrame(rows,columns=['river','stn','fema1pct','model']).drop_duplicates(['river','stn']).sort_values(['river','stn'])
df['diff']=df.model-df.fema1pct
print(df.groupby('river')['diff'].describe().round(2)); print(df.to_string())
try:
    print(f['Results/Unsteady/Summary'].attrs.get('Computation Time Total'), f['Results/Unsteady/Summary'].attrs.get('Solution'))
except Exception as e: print(e)
