# Import GEE & initialize
import ee
try:
    ee.Initialize()
except Exception as e:
    ee.Authenticate()
    ee.Initialize()

# import geetools
# import geemap

asset_location = "projects/ee-abnatcap/assets/sargassum/"
nearshore_mask = ee.FeatureCollection("projects/ee-abnatcap/assets/sargassum/S2_sargassum_mask")


image_dates = ['2019-02-26', '2019-04-02', '2019-05-07', '2019-06-26', '2019-09-14', '2019-11-18', '2019-12-03']

for dt in image_dates:
    # -- Dates
    image_date = ee.Date(dt)  # Date of Sentinel-2 image to be classified
    image_date_string = image_date.format('YYYY-MM-dd').getInfo()
    image_date_string_short = image_date.format('YYYYMMdd').getInfo()
    print(image_date_string_short)

    image_source = asset_location + 'classclipped_' + image_date_string_short
    classed_mosaic = ee.Image(image_source)
    image_prj = classed_mosaic.select('sargassum').projection()
    # print(classed_mosaic.getInfo())

    ## Accuracy Assessment Random Samples
    print('Creating AA points..')
    aaPoints = classed_mosaic.stratifiedSample(
        numPoints=100,
        classBand='sargassum',
        projection=image_prj,
        scale=10,
        region=nearshore_mask.geometry(), #.getInfo()['coordinates'],
        dropNulls=False,
        geometries=True
    )
    print(aaPoints.size().getInfo())
    # Only include Present or Absent points, remove cloud masked and no data areas
    aaPoints = aaPoints.filter(ee.Filter.gte('sargassum',0))
    print(aaPoints.size().getInfo())

    # ******************** Export *****************************
    output_folder = 'sargassum/aa/'

    ## Export Accuracy Assessment Points
    output_layer = 'aaPoints_' + image_date_string_short
    task = ee.batch.Export.table.toDrive(collection=aaPoints,
                                         description=output_layer,
                                         folder=output_folder,
                                         fileFormat='SHP')
    task.start()

