// Habitat-Flood Flexible Model (HFFM)
// Historical pluvial indicators from ERA5-Land daily precipitation.
// Period: 1990-2019. Native calculation grid: 0.1 degree, EPSG:4326.
// R95d uses the 1990-2019 P95 climatology with a 10 mm floor.
// Rx5day is the annual maximum consecutive 5-day precipitation.

var globalROI = ee.Geometry.Rectangle([-180, -60, 180, 85], 'EPSG:4326', false);
var startYear = 1990;
var endYear = 2019;
var exportFolder = 'HFFM_Covariates_01deg';

var era5Daily = ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR')
  .select('total_precipitation_sum')
  .filterDate('1990-01-01', '2020-01-01')
  .map(function(img) {
    return img.multiply(1000).rename('precip_mm').toFloat()
      .copyProperties(img, ['system:time_start']);
  });

var climatologyP95 = era5Daily.reduce(ee.Reducer.percentile([95])).rename('clim_p95');
var minExtremePrecip = ee.Image(10.0);
var finalThreshold = climatologyP95.max(minExtremePrecip);

for (var year = startYear; year <= endYear; year++) {
  var startDate = ee.Date.fromYMD(year, 1, 1);
  var endDate = ee.Date.fromYMD(year + 1, 1, 1);
  var daysInYear = endDate.difference(startDate, 'day').getInfo();
  var yrDaily = era5Daily.filterDate(startDate, endDate);

  var R95d = yrDaily.map(function(img) {
    return img.gt(finalThreshold).toInt();
  }).sum().toInt().rename('R95d');

  var windowOffsets = ee.List.sequence(0, daysInYear - 5);
  var rolling5Sums = ee.ImageCollection.fromImages(windowOffsets.map(function(offset) {
    var windowStart = startDate.advance(offset, 'day');
    var windowEnd = windowStart.advance(5, 'day');
    return yrDaily.filterDate(windowStart, windowEnd).sum()
      .set('system:time_start', windowStart.millis());
  }));
  var Rx5day = rolling5Sums.max().toFloat().rename('Rx5day');

  var pluvialFlood = ee.Image.cat(R95d, Rx5day).clip(globalROI).unmask(0.0).toFloat();

  Export.image.toDrive({
    image: pluvialFlood,
    description: 'HFFM_Pluvial_Flood_' + year + '_01deg',
    folder: exportFolder,
    scale: 11132,
    crs: 'EPSG:4326',
    region: globalROI,
    maxPixels: 1e13,
    fileFormat: 'GeoTIFF',
    formatOptions: {cloudOptimized: true}
  });
}
