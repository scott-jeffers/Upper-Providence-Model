#!/bin/bash
# export every finished river plan to the dashboard + calibration table
cd ~/up/web
M=$HOME/mnt/Upper-Providence-Model/Model/UpperProvidence
ids=(riv_q12k riv_2yr riv_5yr riv_10yr riv_25yr riv_50yr riv_100yr riv_500yr riv_ida2021 riv_agnes1972)
for k in $(seq 1 10); do p=$(printf "p%02d" $k); id=${ids[$((k-1))]}; h=$M/UpperProvidence.$p.hdf
  [ -f $h ] || continue
  python3 -c "import h5py,sys;f=h5py.File('$h','r');s=f['Results/Unsteady/Summary'].attrs.get('Solution',b'');sys.exit(0 if b'Success' in s else 1)" 2>/dev/null || { echo "$p not finished"; continue; }
  [ -f $HOME/mnt/Upper-Providence-Model/Dashboard/data/scenarios/$id.js ] && [ $HOME/mnt/Upper-Providence-Model/Dashboard/data/scenarios/$id.js -nt $h ] && { echo "$p exported"; continue; }
  name=$(python3 -c "import json;print(json.load(open('$HOME/up/scenarios_up.json'))[$k-1]['title'])")
  timeout 170 python3 export_scenario_up.py $h $id "$name" --meta "{\"kind\":\"river\",\"plan\":\"$p\"}" 2>&1 | grep -v -i "warn\|ogr" | tail -1
done
python3 build_index_up.py
