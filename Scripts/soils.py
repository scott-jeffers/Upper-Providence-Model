import requests,json,geopandas as gpd
from shapely import wkt
d=gpd.read_file('domain.geojson').to_crs(4326)
x0,y0,x1,y1=d.buffer(0.003).total_bounds
poly=f"POLYGON(({x0} {y0},{x1} {y0},{x1} {y1},{x0} {y1},{x0} {y0}))"
q=f"""SELECT mp.mukey, ma.hydgrpdcd, ma.muname, mp.mupolygongeo.STAsText() AS wkt
FROM mupolygon mp INNER JOIN muaggatt ma ON ma.mukey=mp.mukey
WHERE mp.mupolygongeo.STIntersects(geometry::STGeomFromText('{poly}',4326))=1"""
r=requests.post('https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest',data={'query':q,'format':'JSON+COLUMNNAME'},timeout=160)
print(r.status_code,len(r.text))
t=r.json()['Table']; cols=t[0]; rows=t[1:]
g=gpd.GeoDataFrame([dict(zip(cols[:3],x[:3])) for x in rows],geometry=[wkt.loads(x[3]) for x in rows],crs=4326)
g.to_file('soils.geojson'); print(len(g)); print(g.hydgrpdcd.value_counts(dropna=False))
