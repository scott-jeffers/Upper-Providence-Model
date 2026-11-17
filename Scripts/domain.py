import geopandas as gpd, numpy as np, json
from shapely.ops import linemerge, substring, unary_union
from shapely.geometry import Point, Polygon
z=gpd.read_file('fema_zones.geojson').to_crs(2272)
sel=z[(z.FLD_ZONE.isin(['AE','A']))|(z.ZONE_SUBTY=='0.2 PCT ANNUAL CHANCE FLOOD HAZARD')]; fp=unary_union([g.buffer(0) for g in sel.geometry.make_valid()]).buffer(1)
nhd=gpd.read_file('nhd_flow0.geojson').to_crs(2272)
loc=gpd.read_file('local_drainage.geojson').geometry.iloc[0]
lims={'Schuylkill River':(9.6,21.0),'Perkiomen Creek':(8.8,15.08)}
parts=[loc]; secs={}
for nm,(a,b) in lims.items():
    L=linemerge(nhd[nhd.gnis_name==nm].union_all())
    if L.geom_type!='LineString': L=max(L.geoms,key=lambda g:g.length)
    s=substring(L,a*5280,min(b*5280,L.length)); secs[nm]=s
    corr=s.buffer(3500,cap_style=2)
    parts.append(fp.intersection(corr).buffer(150).intersection(corr))
    parts.append(s.buffer(250,cap_style=2))
dom=unary_union(parts).buffer(200).buffer(-200)
if dom.geom_type=='MultiPolygon': dom=max(dom.geoms,key=lambda g:g.area)
dom=Polygon(dom.exterior).simplify(20)
gpd.GeoDataFrame({'name':['UP_domain']},geometry=[dom],crs=2272).to_file('domain.geojson')
gpd.GeoDataFrame({'name':list(secs)},geometry=list(secs.values()),crs=2272).to_file('river_sections.geojson')
print('domain sqmi',round(dom.area/27878400,2), 'bounds',dom.bounds)
