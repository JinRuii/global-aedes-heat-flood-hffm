# HFFM code for global Aedes-borne arboviral risk frontiers

Code supporting the manuscript:

**Compound heat-flood thresholds reshape global Aedes-borne arboviral risk frontiers**

This repository reproduces the Habitat-Flood Flexible Model (HFFM): historical thermal and flood indices, surveillance-bias adjustment, model fitting, five-state classification, future projection and climate-population decomposition.

Processed data are archived separately on Zenodo. This repository contains code only.

## Analysis in brief
- Response: annual 0.5-degree occurrence of dengue, chikungunya or Zika (DCZ), 1990-2019.
- Climate drivers: thermal suitability index (TSI), flood activation index (FAI) and overheat suppression days (OHD).
- Model: binomial GAM with a tensor-product smooth of TSI and FAI, plus a surveillance offset.
- States: cold-limited, heat-constrained, water-limited, flushing-limited, compound-suitable.
- Futures: SSP1-2.6, SSP3-7.0 and SSP5-8.5, 2020-2100.

## Repository layout
    gee/     Google Earth Engine scripts for historical TSI, OHD, R95d and Rx5day
    python/  surveillance offset, FAI, future FAI, five-state classification, exposure decomposition
    r/       HFFM fit, three-way interactions, future prediction
    docs/    method notes mapped to the manuscript

## Requirements
- Google Earth Engine account for `gee/`
- Python 3.10+ (`environment.yml` or `requirements.txt`)
- R 4.3+ with `mgcv`, `data.table`, `ggplot2`

## Data needed to run the pipeline
Download the Zenodo deposit after it is published and place it outside this repository, or point the commands below to its `data/` folder.

Minimum files:
- `data/01_historical_panel/Panel_with_IPCC_Region_FINAL.csv`
- `data/04_thresholds/region_flood_thresholds_final.csv`
- `data/02_future_projections/inputs/step1_SSP*_prepared.csv`

Raw ERA5-Land, GloFAS, NEX-GDDP-CMIP6, ISIMIP and H08 archives are not stored here. See `docs/DATA_AND_METHODS.md`.

## Run order
1. Historical climate indicators (optional if using the Zenodo panel):
   - `gee/01_thermal_suitability.js`
   - `gee/02_pluvial_indicators.js`
   Aggregate the 0.1-degree exports to the 0.5-degree study grid.
2. Surveillance offset:
   `python python/01_surveillance_offset.py --input PANEL.csv --output PANEL_with_offset.csv`
3. Historical FAI:
   `python python/02_flood_activation_index.py --historical PANEL_with_offset.csv --output PANEL_with_FAI.csv --params-out outputs/fai_params.json`
4. Fit HFFM:
   `Rscript r/01_fit_hffm.R PANEL_with_FAI.csv outputs/hffm_model.rds`
5. Optional interaction models:
   `Rscript r/02_three_way_interactions.R PANEL_with_FAI.csv outputs/interactions`
6. Future FAI, if rebuilding future hydrology rather than using Zenodo step1 files:
   `python python/03_future_fai.py --historical PANEL_with_FAI.csv --params outputs/fai_params.json --river-dir PATH --rain-dir PATH --output-dir outputs/future_fai`
7. Future probabilities:
   `Rscript r/03_predict_future.R outputs/hffm_model.rds step1_SSP1_prepared.csv outputs/step2_SSP1_with_prob.csv`
8. Five-state classification:
   `python python/05_five_state_classification.py --input outputs/step2_SSP1_with_prob.csv --thresholds region_flood_thresholds_final.csv --output outputs/states_SSP1.csv`
9. Exposure decomposition:
   `python python/06_shapley_exposure.py --pred decomp_pred_SSP1.csv --states outputs/states_SSP1.csv --output outputs/exposure_SSP1.csv`

## Mapping to the manuscript
- Fig. 1: `python/01_surveillance_offset.py` and `r/01_fit_hffm.R`
- Fig. 2: `r/01_fit_hffm.R`, `r/02_three_way_interactions.R`, `python/05_five_state_classification.py`
- Fig. 3: `r/03_predict_future.R` and `python/05_five_state_classification.py`
- Fig. 4 and Table 1: `python/06_shapley_exposure.py`
- Table 2: counterfactual columns in `decomp_data_SSP*.csv` / `decomp_pred_SSP*.csv`

Thermal thresholds used in classification: TSI 77.8 and 236.1. Global FAI water threshold: 0.24. Uncalibrated regions use x_r = 0.407. File tags SSP1 / SSP3 / SSP5 correspond to SSP1-2.6 / SSP3-7.0 / SSP5-8.5.
