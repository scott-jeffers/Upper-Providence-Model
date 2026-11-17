import json,os
D=os.path.expanduser('~/mnt/Upper-Providence-Model/Dashboard/data/')
sc=json.load(open(os.path.expanduser('~/up/scenarios_up.json')))
ids=['riv_q12k','riv_2yr','riv_5yr','riv_10yr','riv_25yr','riv_50yr','riv_100yr','riv_500yr','riv_ida2021','riv_agnes1972']
cat=[]
for k,(s,i) in enumerate(zip(sc,ids),1):
    cat.append({'id':i,'plan':f'p{k:02d}','name':s['title'].replace('River ','River flood: ',1),'kind':'river','qS':max(s['qS']),'qP':max(s['qP']),
      'rp':{'riv_2yr':2,'riv_5yr':5,'riv_10yr':10,'riv_25yr':25,'riv_50yr':50,'riv_100yr':100,'riv_500yr':500}.get(i),'depth_in':None,'available':os.path.exists(D+'scenarios/'+i+'.js')})
open(D+'scenarios/index.js','w').write('window.SCENARIO_INDEX='+json.dumps(cat,indent=0)+';\n'); print([(c['id'],c['available']) for c in cat])
