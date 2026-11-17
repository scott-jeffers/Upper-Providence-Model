# Upper Providence River Flood Watch: dashboard

A static web page with no build step. Open `index.html` directly, or host the `Dashboard/` folder on any static web host. GitHub Pages serves it from the main branch at https://scott-jeffers.github.io/Upper-Providence-Model/Dashboard/.

## What it shows
- **Rivers:** live stage and the NWS forecast crest at Pottstown (PTNP1), Graterford (GRAP1) and Norristown (NRSP1).
- **Live weather:**
  - radar and a 50-minute radar loop;
  - rain that has fallen (NOAA MRMS);
  - NWS forecast rain (WPC QPF);
  - NWS alerts.
- **Flood map:** HEC-RAS maximum depth from two dropdowns.
  - **River flood:** the river ladder (bankfull through 500-year, Ida 2021, Agnes 1972) and the combined run.
  - **Local storm:** rain falling on the township (Atlas 14, SCS Type II).
  - Both layers can be on at once. The river layer is drawn on top and hides the local layer wherever the river is wet.
  - Lists and counts merge both runs and keep the deeper value at each road, crossing and building.
- **Automatic match:** picks the river run at or above the NWS forecast crest, plus a local storm when forecast rain is about a 2-year storm or larger.
- **Critical only / Everything:** thresholds that control which roads, crossings and buildings are flagged.

| | Critical only | Everything |
|---|---|---|
| Roads | 2 ft+ of water over 150 ft+ (main roads 1 ft+ over 50 ft+) | 1 ft+ over 50 ft+ |
| Crossings under a mapped road | 1 ft+ over the road | ½ ft+ over the road |
| Buildings | 3 ft+ of water alongside | 1½ ft+ |
| Shaded depth | 1 ft+ | ½ ft+ |

- **FEMA flood zones:** the effective NFHL zones (floodway, 1%, 0.2%), embedded in the page.
- **Exports:** a GeoJSON for SARTopo / CalTopo and a CSV of roads to close.

## Data files
- `data/model_layers.js`: model domain, streams, inferred crossings, township, Atlas 14 values and gauge ratings.
- `data/fema_zones.js`: FEMA NFHL flood zones clipped to the model area plus 1 mile.
- `data/scenarios/index.js`: the catalog of scenarios.
- `data/scenarios/<id>.js`: one file per HEC-RAS run, holding the depth image, flooded roads, crossings, buildings and flood extent.

## Updating a scenario
Run these from the scripts in `tools/`:

```
python3 tools/export_scenario_up.py UpperProvidence.pNN.hdf <id> "<name>" --meta '{"kind":"river"}'
python3 tools/build_index_up.py
```

The scripts were written for the Linux workspace used to build the model, so edit the folder paths at the top of each one before using them elsewhere.

## Caveats
These are screening-level model results, not regulatory flood maps.
- **Rivers:** within about 1 ft of FEMA's 1% water levels on average.
- **Local storms:** storm sewers are not modeled, so street ponding is overstated.

See `../README_model.md`.
