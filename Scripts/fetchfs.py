import json,urllib.request,urllib.parse,time,sys,geopandas as gpd
d=gpd.read_file('domain.geojson').to_crs(4326); x0,y0,x1,y1=d.buffer(0.005).total_bounds
BB=f"{x0},{y0},{x1},{y1}"
def fetch(url,name,page=2000,where='1=1',fields='*'):
    import os
    st=name+'.part.json'
    feats,off=(json.load(open(st)) if os.path.exists(st) else ([],0))
    t0=time.time()
    while True:
        q=dict(where=where,geometry=BB,geometryType='esriGeometryEnvelope',inSR=4326,spatialRel='esriSpatialRelIntersects',outFields=fields,outSR=4326,f='geojson',resultOffset=off,resultRecordCount=page)
        for t in range(5):
            try: r=json.load(urllib.request.urlopen(url+'/query?'+urllib.parse.urlencode(q),timeout=150)); break
            except Exception as e: print('retry',name,off,e,file=sys.stderr); time.sleep(5)
        else: raise SystemExit('fail '+name)
        fs=r.get('features',[]); feats+=fs
        if len(fs)<page and not r.get('properties',{}).get('exceededTransferLimit'): break
        off+=len(fs)
        json.dump([feats,off],open(st,'w'))
        if time.time()-t0>140: print('PARTIAL',name,off); return
        if not fs: break
    json.dump({'type':'FeatureCollection','features':feats},open(name,'w')); print(name,len(feats))
which=sys.argv[1]
D='https://arcgis.dvrpc.org/portal/rest/services/'
if which=='lulc': fetch(D+'Planning/dvrpc_landuse_2023/FeatureServer/0','lulc2023.geojson')
if which=='impmont': fetch(D+'structures/impervious_2015_montgomery/FeatureServer/0','imperv_mont.geojson')
if which=='impches': fetch(D+'structures/impervious_2015_chester/FeatureServer/0','imperv_ches.geojson')
if which=='nbi': fetch('https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services/NTAD_National_Bridge_Inventory/FeatureServer/0','nbi.geojson')

if which=='roads':
    B='https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Transportation/MapServer/'
    for n,l in [('primary',2),('secondary',6),('local',8),('rail',9)]: fetch(B+str(l),'tiger_'+n+'.geojson',page=1000)
if which=='nhdarea':
    B='https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer/'
    fetch(B+'9','nhd_area.geojson',page=500); fetch(B+'12','nhd_wb.geojson',page=500); fetch(B+'0','nhd_pt.geojson',page=500)
