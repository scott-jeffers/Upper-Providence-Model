import json,os,geopandas as gpd,numpy as np
D=os.path.expanduser('~/mnt/Upper-Providence-Model/Dashboard/data/'); U=os.path.expanduser('~/up/')
def fc(g,props=None,simp=0):
    g=g.to_crs(4326)
    if simp: g['geometry']=g.geometry.simplify(simp)
    return json.loads(g[[*(props or []),'geometry']].to_json(drop_id=True))
dom=gpd.read_file(U+'perimeter_up.gpkg')
fl=gpd.read_file(U+'nhd_flow0.geojson'); fl=fl[fl.gnis_name.notna()].to_crs(2272); fl=fl[fl.intersects(dom.geometry.iloc[0].buffer(2000))]; fl['name']=fl.gnis_name
cu=gpd.read_file(U+'culverts_up.gpkg'); cu['geometry']=cu.geometry.centroid
A=json.load(open(U+'atlas14.json')); durs=list(A.keys()); rps=[1,2,5,10,25,50,100,200,500,1000]
c=dom.to_crs(4326).geometry.iloc[0].centroid
L={'watershed':fc(dom,['name'],0.00005),'streams':fc(fl,['name'],0.00003),'crossings':fc(cu,['cid','type','road','da_ac','notch_w_ft']),
   'pipes':{'type':'FeatureCollection','features':[]},'outfalls':{'type':'FeatureCollection','features':[]},
   'municipalities':fc(gpd.read_file(U+'township.geojson').assign(name='Upper Providence Twp'),['name'],0.00005),
   'atlas14':{'rp':rps,'dur':[d.replace('min','-min') if d.endswith('min') and d!='60min' else ('60-min' if d=='60min' else d.replace('hr','-hr').replace('day','-day')) for d in durs],'depth':[[A[d][str(r)] if str(r) in A[d] else A[d][r] for r in rps] for d in durs],'lat':round(c.y,5),'lon':round(c.x,5)},
   'gauges':json.load(open(U+'gauge_ratings.json'))}
os.makedirs(D+'scenarios',exist_ok=True)
open(D+'model_layers.js','w').write('window.MODEL_LAYERS='+json.dumps(L,separators=(',',':'))+';\n')
print(L['atlas14']['dur'], os.path.getsize(D+'model_layers.js')/1e6)
