# Upper Providence Township flood model and dashboard

This repository holds a HEC-RAS 7 2D flood model and a public flood-watch dashboard for Upper Providence Township, Montgomery County, PA. The model covers the Schuylkill River, Perkiomen Creek and the township's local streams.

- **`Dashboard/`**: a static web page showing live river forecasts, radar and rain, NWS alerts, FEMA flood zones and modeled flood depths. Live page: https://scott-jeffers.github.io/Upper-Providence-Model/ (GitHub Pages, served from the main branch).
- **`Model/UpperProvidence/`**: the HEC-RAS project text files (project, geometry, flow and plan files). The large HDF result files and the terrain are not stored here.
- **`Scripts/`**: Python scripts that built the terrain, inferred the culverts, built the mesh and generated the plans.
- **`GIS/`**: the model domain, township boundary and inferred culverts and bridges.
- **`Hydrology/`**: NOAA Atlas 14 rainfall, USGS annual peaks and the fitted gauge ratings.
- **`README_model.md`**: the model setup, calibration and limitations.

## Scenarios
| Group | Runs |
|---|---|
| River floods | Bankfull; 2, 5, 10, 25, 50, 100 and 500-year (both rivers at the same return period); Ida 2021 and Agnes 1972 replays |
| Local storms, 24-hour | 2, 10, 25 and 100-year |
| Local storms, 6-hour | 100-year |
| Combined | 100-year 24-hour rain plus a 10-year flood on both rivers |

## Disclaimer
These are planning and screening results. They are not regulatory flood maps and do not replace FEMA Flood Insurance Rate Maps. In a real flood, follow official National Weather Service warnings and emergency management instructions.
