# Upper Providence Township – HEC-RAS 2D river flood model (v1)

Folder: `Upper-Providence-Model`

## What's in here
| Folder | Contents |
|---|---|
| `Model/UpperProvidence/` | HEC-RAS 7.0.1 project (`UpperProvidence.prj`), 1 geometry, 10 river-flood plans |
| `Terrain/` | `UP_DEM_1m_ft_hydro.tif` – USGS 1 m lidar (6 tiles, PA 17-County 2024) in PA South ft, with estimated river bathymetry and lidar-inferred culverts/bridges burned in. `raw/` = original tiles |
| `GIS/base/` | DVRPC 2023 land use, DVRPC 2015 impervious/buildings, NRCS soils (HSG), NBI bridges, TIGER roads/rail, NHD flowlines |
| `GIS/FEMA/` | FEMA NFHL zones, cross sections (1% WSEL), BFEs – used for the domain and calibration |
| `GIS/structures/` | `culverts_up.gpkg/.csv` – 281 inferred crossings (163 pipes, 87 boxes, 21 estimated bridges/boxes, 10 matched to NBI). 25 long (>300 ft) candidates were dropped and are listed separately |
| `Hydrology/` | Atlas 14 (domain centroid), USGS annual peaks, fitted stage-flow ratings for Pottstown, Graterford, Norristown |
| `Dashboard/` | Flood-watch web page (open `index.html`) |
| `Scripts/` | Every processing script, so the build can be repeated |

## Model setup
- One 2D area, 27.7 sq mi, about 116,700 cells. Cells are about 100 ft in the uplands, 60 ft in FEMA floodplains and 40 ft in the river channels, with cell faces aligned to the river banks.
- Domain = the township's local drainage, plus the FEMA 1% / 0.2% floodplain of the Schuylkill (river miles about 9.6–21) and the Perkiomen (lower 6.3 mi).
- Boundary conditions:
  - Schuylkill US: flow hydrograph, EG slope 0.0005.
  - Perkiomen US: flow hydrograph, EG slope 0.001.
  - Schuylkill DS (Valley Forge): stage hydrograph from a normal-depth rating of the lidar section (S = 0.0006).
- Manning's n comes from land cover; channel 0.035. Infiltration is SCS CN by land cover and HSG. Rain is off in the river plans.
- Solver: Diffusion Wave, Courant-controlled time step (max Courant 3, max 40 s). The 2 h IC ramp is followed by 2 h of base flow, a 4 h rise and 8 h at peak, so the result is effectively steady-state at the peak.

## Plans (river levels assumed to coincide on both rivers)
| Plan | Schuylkill US (cfs) | Perkiomen US (cfs) |
|---|---|---|
| p01 Bankfull-ish | 12,240 | 6,000 |
| p02 2-yr | 21,100 | 16,700 |
| p03 5-yr | 31,300 | 25,600 |
| p04 10-yr | 39,200 | 32,400 |
| p05 25-yr | 50,300 | 41,800 |
| p06 50-yr | 59,600 | 49,500 |
| p07 100-yr | 69,700 | 57,800 |
| p08 500-yr | 97,100 | 79,800 |
| p09 Ida 2021 | 37,100 | 64,400 (record) |
| p10 Agnes 1972 | 97,800 | 35,800 |

Return-period flows come from a log-Pearson III fit to USGS peaks: Pottstown (01472000) ×1.02 for drainage area, and Graterford (01473000) post-1956, after Green Lane Dam. These are screening estimates, not Bulletin 17C or FIS values.

NWS flood stages and approximate flows, from ratings fitted to USGS peaks:

| Gauge | Action | Minor | Moderate | Major |
|---|---|---|---|---|
| Graterford (GRAP1) | 8 ft ≈ 8.4k cfs | 11 ft ≈ 14.9k | 13 ft ≈ 20.5k | 16 ft ≈ 30.5k |
| Pottstown (PTNP1) | 11 ft ≈ 18k | 12.5 ft ≈ 22k | 18 ft ≈ 40k | 22 ft ≈ 56k |
| Norristown (NRSP1) | 12 ft | 13 ft | 17 ft | 19 ft |

## Known limitations
- The river bathymetry is estimated, because the lidar is hydro-flattened. Depth below the lidar water surface scales with channel half-width, up to 7 ft.
- Culverts and bridges are notches in the terrain (no pressure or deck losses). Sizes are inferred from drainage area with a 10-yr rational method.
- Black Rock and Vincent dams are represented only by the lidar water-surface step.
- Tributaries entering from outside the domain on the far bank are not included as inflows.
- Coincident AEP on both rivers is conservative for joint events.
- Calibration against FEMA 1% WSELs is pending. Run `Scripts/calcheck.py p07` after the 100-yr plan finishes.
