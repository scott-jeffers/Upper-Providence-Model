import requests,json,sys,time
which=sys.argv[1]
if which=='a14':
    import geopandas as gpd
    c=gpd.read_file('domain.geojson').to_crs(4326).geometry.iloc[0].centroid
    r=requests.get('https://hdsc.nws.noaa.gov/cgi-bin/new/cgi_readH5.py',params=dict(lat=round(c.y,4),lon=round(c.x,4),type='pf',data='depth',units='english',series='pds'),timeout=60)
    open('a14.txt','w').write(r.text); print(c.y,c.x,r.status_code,r.text[:600])
if which=='peaks':
    for s in ['01473000','01472000','01472157','01473500','01474500']:
        r=requests.get('https://nwis.waterdata.usgs.gov/nwis/peak',params=dict(site_no=s,agency_cd='USGS',format='rdb'),timeout=60)
        open(f'peaks_{s}.rdb','w').write(r.text)
        L=[l for l in r.text.splitlines() if l.startswith('USGS')]
        print(s,r.status_code,len(L),L[-1][:80] if L else '')
if which=='site':
    r=requests.get('https://waterservices.usgs.gov/nwis/site/',params=dict(sites='01473000,01472000,01472157,01473500,01474500',format='rdb',siteOutput='expanded'),timeout=60)
    for l in r.text.splitlines():
        if l.startswith('USGS'): f=l.split('\t'); print(f[1],f[2],f[6],f[7],f[29] if len(f)>29 else '')
