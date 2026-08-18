// Habitat-Flood Flexible Model (HFFM)
// Historical thermal suitability from ERA5-Land daily 2-m temperature.
// Period: 1990-2019. Native calculation grid: 0.1 degree, EPSG:4326.
// Export annual GeoTIFFs, then aggregate to the 0.5-degree study grid.

var globalROI = ee.Geometry.Rectangle([-180, -60, 180, 85], 'EPSG:4326', false);
var startYear = 1990;
var endYear = 2019;
var tMin = 14;   // developmental lower bound, deg C
var tOptLo = 25; // lower edge of the transmission plateau
var tOptHi = 30; // upper edge of the transmission plateau
var tMax = 35;   // upper lethal / suppression bound
var tHot = 35;   // overheat-suppression threshold used for OHD

var computeThermalSuitability = function(image) {
  var t = image.select('temperature_2m').subtract(273.15).toFloat();

  var suit = t.where(t.lt(tMin), 0.0)
              .where(t.gt(tMax), 0.0)
              .where(t.gte(tMin).and(t.lt(tOptLo)), t.subtract(tMin).divide(tOptLo - tMin))
              .where(t.gte(tOptLo).and(t.lte(tOptHi)), 1.0)
              .where(t.gt(tOptHi).and(t.lte(tMax)), ee.Image.constant(tMax).subtract(t).divide(tMax - tOptHi))
              .toFloat();

  var overheat = t.gt(tHot).toFloat().rename('overheat_day');
  return image.addBands(suit.rename('suit')).addBands(overheat);
};

var era5 = ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR');

for (var year = startYear; year <= endYear; year++) {
  var filtered = era5
    .filter(ee.Filter.calendarRange(year, year, 'year'))
    .map(computeThermalSuitability);

  var integral = filtered.select('suit').sum().toFloat()
    .rename('thermal_suitability_integral');
  var suitableDays = filtered.select('suit').map(function(img) {
    return img.gt(0).toFloat();
  }).sum().toFloat().rename('thermal_suitable_days');
  var overheatDays = filtered.select('overheat_day').sum().toFloat()
    .rename('overheat_penalty_days');

  var out = integral.addBands(suitableDays).addBands(overheatDays)
    .clip(globalROI).unmask(0.0);

  Export.image.toDrive({
    image: out,
    description: 'HFFM_Thermal_Indices_' + year,
    folder: 'HFFM_Covariates_01deg',
    scale: 11132,
    crs: 'EPSG:4326',
    region: globalROI,
    maxPixels: 1e13,
    fileFormat: 'GeoTIFF'
  });
}
