# Import GEE & initialize
import ee
try:
    ee.Initialize()
except Exception as e:
    ee.Authenticate()
    ee.Initialize()

asset_location = "projects/ee-abnatcap/assets/sargassum/"

image_dates = ['2019-02-26', '2019-04-02', '2019-05-07', '2019-06-26', '2019-09-14', '2019-11-18', '2019-12-03']
# image_dates = ['2019-02-26']

image_level = ['']
# image_level = ['sr_','toa_']
# image_level = ['toa_']
# image_level = ['sr_']

for level in image_level:
    for dt in image_dates:
        # -- Dates in various formats
        image_date = ee.Date(dt)  # Date of classified Sentinel-2
        image_date_string = image_date.format('YYYY-MM-dd').getInfo()
        image_date_string_short = image_date.format('YYYYMMdd').getInfo()
        print(image_date_string_short)

        # AA points to sample
        aa_points_source = asset_location + 'aaPoints_' + image_date_string_short + '_validated'
        aa_points = ee.FeatureCollection(aa_points_source)
        # print(aa_points.getInfo())

        # Classified image
        classed_source = asset_location + 'classclipped_' + level + image_date_string_short
        classified = ee.Image(classed_source)
        image_prj = classified.select('sargassum').projection()
        print(classed_source)
        # print(image_prj.getInfo())
        sargassum = classified.select(["sargassum"],[level + 'sarg']).eq(1).selfMask()   # raster with just sargassum

        # Sample Classified values at each AA point location
        print('Sampling Classified Image....')
        sargassum_samples = sargassum.sampleRegions(**{
            'collection': aa_points,
            'properties': ['aa_id'],  # ,'validclass','classdesc','validpa'],
            'scale': 10,
            'geometries': True
        })
        # print(sargassum_samples.first().propertyNames().getInfo())

        # Create patch ID for sargassum only
        print("Creating Unique Sargassum Patch Ids....")
        sargassum_patches = sargassum.connectedComponents(
            connectedness=ee.Kernel.square(1), maxSize=1024).select(['labels'],[level + 'patch'])  # .square(1) = eight-neighbor connections
        # print(sargassum_patches.bandNames().getInfo())
        # patch_count = sargassum_patches.reduce(ee.Reducer.countDistinct())
        # print(patch_count.bandNames().getInfo())
        # print(patch_count.getInfo())
        # patch_count_maxmin = patch_count.reduce(ee.Reducer.minMax())
        # print(patch_count_maxmin.getInfo())

        # Reduce the region. The region parameter is the Feature geometry.
        print("Getting Count of Unique Patches...")
        countDictionary = sargassum_patches.reduceRegion(**{
            'reducer': ee.Reducer.countDistinct(),
            'geometry': sargassum_patches.geometry(),
            'scale': 10,
            'maxPixels': 1e12
        })
        print(countDictionary.getInfo())


        # Sample the Patches with Accuracy Assessment points
        # Overlay the points on the imagery to get training.
        patch_samples = sargassum_patches.sampleRegions(**{
            'collection': sargassum_samples,
            # 'properties': ['aa_id'],
            'scale': 10,
            'geometries': True
        })

        print(patch_samples.first().propertyNames().getInfo())
        # print(patch_samples.first().getInfo())

        # # ******************** Export *****************************
        output_folder = 'aa/'  # r'sargassum/aa/'
        #
        # ## Export Accuracy Assessment Points
        # output_layer = 'aaPatches_' + level + image_date_string_short
        # print('Output Layer: ' + output_layer)
        # task = ee.batch.Export.table.toDrive(collection=patch_samples,
        #                                      description=output_layer,
        #                                      folder=output_folder,
        #                                      fileFormat='SHP')
        # task.start()



