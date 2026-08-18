# Method notes aligned to the manuscript

Manuscript title: Compound heat-flood thresholds reshape global Aedes-borne arboviral risk frontiers
Model name in the manuscript: Habitat-Flood Flexible Model (HFFM)

## Historical climate, 1990-2019
- Daily 2-m air temperature and precipitation: ERA5-Land.
- Daily river discharge: GloFAS-ERA5 v4.0.
- Indicators were calculated at 0.1 degree in Google Earth Engine and aggregated to the 0.5-degree study grid by cell-area averaging.

## Future climate, 2020-2100
- Temperature: NEX-GDDP-CMIP6.
- Precipitation: ISIMIP3b W5E5.
- Discharge: H08, empirically quantile-mapped to GloFAS-ERA5 over 2015-2019.
- Scenarios: SSP1-2.6, SSP3-7.0, SSP5-8.5. File tags SSP1 / SSP3 / SSP5 follow this order.

## Thermal suitability
Daily suitability S(T) is 0 at or below 14 C, rises linearly to 1 at 25 C, stays at 1 through 30 C, declines linearly to 0 at 35 C, and is 0 above 35 C. Annual TSI is the sum of daily S(T). OHD counts days above 35 C. These bounds match the GEE script and the manuscript piecewise function.

## Flood activation index
FAI is PC1 of four indicators: high-discharge days above historical Q95, annual maximum discharge, heavy-precipitation days above historical P95 and 10 mm, and Rx5day. Historical z-scores, loadings, 3-sigma truncation and min-max limits are frozen and reused for future years. An earlier two-variable MinMax draft is not used.

## Surveillance offset
Binomial logistic model of DCZ occurrence on healthcare travel time, GDP per capita and built-up fraction, fitted only where |latitude| <= 53.75. The predicted probability is clipped to [0.001, 0.999] and converted to log-odds. Future years keep the 2019 offset.

## HFFM
Binomial GAM / bam with:
logit(p) = te(TSI, FAI) + s(OHD) + s(year) + te(lon, lat) + s(NDVI) + s(elevation) + s(log population) + offset(logit(q))

In the fitting script, TSI enters as `thermal_scaled` and FAI as `flood_scaled`.

## Five states
- cold: TSI < 77.8
- heat: TSI > 236.1
- water: 77.8 <= TSI <= 236.1 and FAI < 0.24
- flushing: 77.8 <= TSI <= 236.1 and 0.24 <= FAI < max(0.24, x_r)
- compound: 77.8 <= TSI <= 236.1 and FAI >= max(0.24, x_r)

Uncalibrated IPCC regions use x_r = 0.407.

## Exposure
Probability-weighted exposure is the sum, over compound-suitable cells, of predicted probability x population density x grid-cell area. Climate and population effects are the symmetric Shapley averages defined in manuscript Table 2.

## What is not in this repository
Author names, local Windows paths, the manuscript file, figure artwork, and raw third-party climate archives.
