# Import GEE & initialize
import ee
try:
    ee.Initialize()
except Exception as e:
    ee.Authenticate()
    ee.Initialize()

# import geetools
import geemap

# Image and cloud sources
# s2_source = 'COPERNICUS/S2_SR'  # Surface Reflectance
s2_source = 'COPERNICUS/S2'  # Top of Atmosphere
s2_clouds_source = 'COPERNICUS/S2_CLOUD_PROBABILITY'
asset_location = 'projects/ee-abnatcap/assets/sargassum/'

# Data sources (other than S2)
SRTM = ee.Image("USGS/SRTMGL1_003")
# samples = ee.FeatureCollection(asset_location + "samples_S2sr_20190507_allbands") # Surface Reflectance
# samples = ee.FeatureCollection(asset_location + "samples20190507_16QDH_allbands") # Surface Reflectance
# samples = ee.FeatureCollection(asset_location + "samples_S2toa_20190507_allbands")  # Top of Atmosphere v1
# samples = ee.FeatureCollection(asset_location + "samples_S2toa_20190507_allbands_v2")  # Top of Atmosphere v2
samples = ee.FeatureCollection(asset_location + "samples_S2toa_20190507_allbands_v3")  # Top of Atmosphere v3

# classes = ee.FeatureCollection(asset_location + "trainingsites20190507")
nearshore_mask = ee.FeatureCollection("projects/ee-abnatcap/assets/sargassum/S2_sargassum_mask")

# Export Locations
# output_folder = 's2sr_classified'   # Surface Reflectance
# output_folder = 's2toa_classified_v1'   # Top of Atmosphere v1
output_folder = 's2toa_classified_v3'   # Top of Atmosphere v3

# Image masking thresholds
ndvi_threshold = 0.0
elevation_threshold = 10
swm_threshold = 1.4

# ---- Bands & Indices
# Relevant Bands B2=blue, B3=green, B4=red, B8=NIR, B11,B12=SWIR, QA60=cloud mask
#  B5, B6, B7 = red Edge (20m), B8A = NIR narrow wavelength, 20m res
# S2bands = ee.List(['B2','B3','B4','B5','B6','B7','B8','B8A','B11','B12','QA60'])
S2bands = ee.List(['B2', 'B3', 'B4', 'B5', 'B8', 'B8A', 'B11', 'B12', 'QA60'])

S2bands_spectral = ee.List(S2bands).remove('QA60')
BLUE = 'B2'  # 490 nmn, 10m
GREEN = 'B3'  # 560 nm, 10m
RED = 'B4'  # 665 nm, 10m
REDEDGE1 = 'B5'  # 705 nm, 20m
REDEDGE2 = 'B6'  # 740 nm, 20m
REDEDGE3 = 'B7'  # 783 nm, 20m
NIR = 'B8'  # 842 nm, 10m
NIR2 = 'B8A'  # 865 nm, 20m
SWIR1 = 'B11'  # 1610nm, 20m
SWIR2 = 'B12'  # 2190 nm, 20m

NDVI = "NDVI"
indices = ["NDVI", "SAVI", "FAI", "AFAI", "SEI"]

# ********************* Study Region  *************************************************

# Quintana Roo rectangular extent
QR_boundbox = ee.Geometry.Rectangle(-88.0, 18.1, -86.6, 21.7)

# POint locations for QR S-2 Tiles, 16QDJ, 16QEJ, 16QDH, 16QEH, 16QDG, 16QDF
QR_multipoint = ee.Geometry.MultiPoint(
    [[-87.4, 21.2], [-86.6, 21.2], [-87.4, 20.3], [-86.6, 20.3], [-87.4, 19.3], [-87.4, 18.3]])
# print(QR_multipoint)


#################################
# Construct Random Forest Model #
#################################

# Prepare training data and predictors
#######################################

# Integer value to indicate land cover class:
lc_code = 'lc_code'
random_column = 'random'  # column to hold random number for splitting into training/testing

# Define the bands you want to include in the model
bands_model = ee.List(['B2', 'B5', 'B8', 'B8A', 'B12', 'FAI', 'SEI', 'NDVI', 'NDVI_median', 'NDVI_min', 'NDVI_dmed'])
# print("Input Bands for Model", bands_model.getInfo())

# Randomly split our samples to set some aside for testing our model's accuracy
# using the "random" column we created
split = 0.8  # Roughly 80% for training, 20% for testing.
training = samples.filter(ee.Filter.lt(random_column, split))  # Subset training data
testing = samples.filter(ee.Filter.gte(random_column, split))  # Subset testing data

# Print these variables to see how much training and testing data you are using
# print('Samples n =', samples.aggregate_count('.all'))
# print('Training n =', training.aggregate_count('.all'))
# print('Testing n =', testing.aggregate_count('.all'))


#  Train Random Forest Classification
# ##################################

# .smileRandomForest is used to run the model. Here we train the model using 100 trees
# and 5 randomly selected predictors per split ("(100,5)")

bands2train = bands_model.add(lc_code)
print("Bands for Training", bands2train.getInfo())

print('Training Random Forest model......')
classifier = ee.Classifier.smileRandomForest(100, 5).train(**{
    'features': training.select(bands2train),  # Train using bands and landcover property
    'classProperty': lc_code,  # Pull the landcover property from classes
    'inputProperties': bands_model
})

# print("RF Explain", classifier.explain().getInfo())  # this explains the feature importance.

# Test the accuracy of the model
##################################
print('Running validation......')
validation = testing.classify(classifier)
testAccuracy = validation.errorMatrix(lc_code, 'classification')
print('Validation error matrix RF: ', testAccuracy.getInfo())
print('Validation overall accuracy RF: ', testAccuracy.accuracy().getInfo())

# ****************** SETUP VARIABLES  **************************************************
# Test dates
# image_dates_test = ['2019-02-26', '2019-04-02', '2019-05-07', '2019-06-26', '2019-09-14', '2019-11-18', '2019-12-03']  # Test Dates

# < 30% cloudy pixel coverage
# 2019
# image_dates_2019 = ['2019-01-12','2019-02-06','2019-02-16','2019-02-26','2019-03-03','2019-03-08','2019-03-23','2019-03-28',
#                '2019-04-02','2019-04-07','2019-04-17','2019-04-22','2019-05-12','2019-05-22','2019-05-27','2019-06-06',
#                '2019-06-26','2019-07-06','2019-07-26','2019-09-04','2019-09-19','2019-09-24','2019-10-24','2019-11-08',
#                '2019-11-18','2019-11-23','2019-12-03','2019-12-23','2019-12-28','2019-05-07', '2019-09-14']
# 2018
# image_dates_2018 = ['2018-01-12','2018-02-06','2018-02-11','2018-02-16','2018-02-21','2018-03-03','2018-03-23','2018-04-02',
#                '2018-04-17','2018-04-22','2018-05-02','2018-05-27','2018-06-06','2018-06-11','2018-06-21','2018-07-11',
#                '2018-07-21','2018-07-26','2018-08-05','2018-08-15','2018-08-25','2018-08-30','2018-09-14','2018-09-29',
#                '2018-10-14','2018-11-13','2018-12-03']
# 2017
# image_dates_2017 = ['2017-03-23','2017-05-02','2017-05-22','2017-09-19','2017-10-09','2017-11-23','2017-12-08','2017-12-13','2017-12-23','2017-12-28']
# 2016
# image_dates_2016 = ['2016-04-27','2016-05-07','2016-06-16','2016-10-14','2016-12-03','2016-12-23']
# 2015
# image_dates_2015 = ['2015-11-19','2015-11-29']

# All dates with < 30% cloudy pixel coverage for at least 5 of the 6 Sentinel-2 image tiles
image_dates_all = ["2015-11-19","2015-11-29", "2016-04-27", "2016-05-07", "2016-06-16", "2016-10-14", "2016-12-03", "2016-12-23", "2017-01-12", "2017-02-01", "2017-02-21", "2017-03-03", "2017-03-23", "2017-05-02", "2017-05-22", "2017-07-01", "2017-08-10", "2017-09-19", "2017-09-24", "2017-10-09", "2017-10-29", "2017-11-23", "2017-12-08", "2017-12-13", "2017-12-23", "2017-12-28", "2018-01-12", "2018-02-01", "2018-02-06", "2018-02-11", "2018-02-16", "2018-02-21", "2018-02-26", "2018-03-03", "2018-03-18", "2018-03-23", "2018-03-28", "2018-04-02", "2018-04-07", "2018-04-17", "2018-04-22", "2018-05-02", "2018-05-07", "2018-05-27", "2018-06-06", "2018-06-11", "2018-06-21", "2018-07-01", "2018-07-11", "2018-07-16", "2018-07-21", "2018-07-26", "2018-07-31", "2018-08-05", "2018-08-15", "2018-08-25", "2018-08-30", "2018-09-14", "2018-09-29", "2018-10-14", "2018-10-24", "2018-11-13", "2018-11-18", "2018-11-23", "2018-12-03", "2018-12-08", "2019-01-12", "2019-02-06", "2019-02-11", "2019-02-16", "2019-02-26", "2019-03-03", "2019-03-08", "2019-03-13", "2019-03-23", "2019-03-28", "2019-04-02", "2019-04-07", "2019-04-12", "2019-04-17", "2019-04-22", "2019-05-07", "2019-05-12", "2019-05-22", "2019-05-27", "2019-06-06", "2019-06-11", "2019-06-21", "2019-06-26", "2019-07-06", "2019-07-26", "2019-08-05", "2019-08-10", "2019-08-25", "2019-09-04", "2019-09-14", "2019-09-19", "2019-09-24", "2019-09-29", "2019-10-14", "2019-10-24", "2019-11-08", "2019-11-18", "2019-11-23", "2019-12-03", "2019-12-23", "2019-12-28"]
# Dates from this set that are supplemental to the dates already run
image_dates = ['2017-01-12', '2017-02-01', '2017-02-21', '2017-03-03', '2017-07-01', '2017-08-10', '2017-09-24', '2017-10-29', '2018-02-01', '2018-02-26', '2018-03-18', '2018-03-28', '2018-04-07', '2018-05-07', '2018-07-01', '2018-07-16', '2018-07-31', '2018-10-24', '2018-11-18', '2018-11-23', '2018-12-08', '2019-02-11', '2019-03-13', '2019-04-12', '2019-05-07', '2019-06-11', '2019-06-21', '2019-08-05', '2019-08-10', '2019-08-25', '2019-09-14', '2019-09-29', '2019-10-14']

for dt in image_dates:
    # -- Dates
    # image_date = ee.Date('2019-05-07')  # Date of Sentinel-2 image to be trained & classified
    image_date = ee.Date(dt)  # Date of Sentinel-2 image to be classified

    # print('S2 Image Date', image_date);
    image_date_string = image_date.format('YYYY-MM-dd').getInfo()
    image_date_string_short = image_date.format('YYYYMMdd').getInfo()
    print(image_date_string_short)

    # Start and end dates for Annual Summary calcs
    image_year = image_date.get('year')
    # print('Year', image_year.getInfo())
    if image_year == 2015:
        image_year = 2016 # don't have a full year of 2015 images, so just use 2016 to compare
    annual_startdate = ee.Date.fromYMD(image_year,1,1) #image_date.advance(-6,'month') -- S2_SR only goes back to 2018-12, so use the calendar year for now
    annual_enddate = ee.Date.fromYMD(image_year,12,31) #image_date.advance(6,'month');

    # Scale the Sentinel-2 Band values
    # https:#mygeoblog.com/2019/09/04/create-a-sentinel-2-for-your-province/
    def scaleBands(image):
        prop = image.toDictionary()  # source image properties
        bands_all = image.bandNames()  # source image bands
        bands2scale = S2bands_spectral  # sprectral bands to be scale
        bands_notscaled = ee.List(bands_all).removeAll(bands2scale)  # Remaining image bands to copy to new image
        myImg = image.select(bands2scale).divide(10000)
        myImg = myImg.addBands(image.select(bands_notscaled)).set(prop).copyProperties(image,['system:time_start', 'system:time_end', 'system:footprint'])
        # myImg = myImg.addBands(image.select(bands_notscaled).copyProperties(image, image.propertyNames())) # Only includes id -- not sure why
        return ee.Image(myImg)

    ## Function to mask clouds using the Sentinel-2 QA band
    ## @param {ee.Image} image Sentinel-2 image
    ## @return {ee.Image} cloud masked Sentinel-2 image
    ## From:  https:#developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2
    def maskCloudsQA(image):
        qa = image.select('QA60')
        # Bits 10 and 11 are clouds and cirrus, respectively.
        cloudBitMask = 1 << 10
        cirrusBitMask = 1 << 11
        # Both flags should be set to zero, indicating clear conditions.
        mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(qa.bitwiseAnd(cirrusBitMask).eq(0))
        return image.updateMask(mask)

    #** Cloud masking with Cloud Probability Layer
    # https:#developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_CLOUD_PROBABILITY
    # -- Max Cloud Probability (for 'COPERNICUS/S2_CLOUD_PROBABILITY')
    MAX_CLOUD_PROBABILITY = 65
    def maskCloudsProb(image):
        clouds = ee.Image(image.select('probability'))
        isNotCloud = clouds.lt(MAX_CLOUD_PROBABILITY)
        return image.updateMask(isNotCloud)

    ## Function to calculate NDVI
    ## @param {ee.Image} image Sentinel-2 image
    ## @return {ee.Image} image with NDVI added Sentinel-2 image
    def addNDVI(image):
        ndvi = image.normalizedDifference([NIR, RED]).rename('NDVI')
        return image.addBands(ndvi)


    # Calculate SAVI - Soil Adjusted Vegetation Index
    # https:#developers.google.com/earth-engine/guides/image_math
    # constant L can be between 0-1, and 0.5 is usually the default
    #    Try varying this to see if it has an effect
    # https:#wiki.landscapetoolbox.org/doku.php/remote_sensing_methods:soil-adjusted_vegetation_index
    # L is the soil brightness correction factor. The value of L varies by the amount or cover of green vegetation:
    # in very high vegetation regions, L=0 and in areas with no green vegetation, L=1.
    # Generally, an L=0.5 works well in most situations and is the default value used. When L=0, then SAVI = NDVI.
    def addSAVI(image):
        savi = image.expression(
            '((NIR - RED) / (NIR + RED + L) * (1 + L))', {
            'L' : 0.5, #* Default L is 0.5
            'NIR': image.select(NIR),
            'RED': image.select(RED),
        }).rename('SAVI')
        return image.addBands(savi)

    # Calculate FAI - Floating Algae Index
    # Hu, 2009
    def addFAI(image):
        fai = image.expression(
            'NIR - (RED + (SWIR - RED) * ((wlNIR - wlRED) / (wlSWIR - wlRED)))', {
            'NIR': image.select(NIR),
            'RED': image.select(RED),
            'SWIR': image.select(SWIR1),
            'wlNIR': 842,  # midpoint wavelength of NIR band in nm
            'wlRED' : 665, # midpoint wavelength of RED band in nm
            'wlSWIR' : 1610,  # midpoint wavelength of SWIR1 band in nm
        }).rename('FAI')
        return image.addBands(fai)


    # Calculate AFAI - Alternative Floating Algae Index
    # Wang & Hu, 2016
    def addAFAI(image):
        afai = image.expression(
            'NIR - (RED + (SWIR - RED) * ((wlNIR - wlRED) / (wlSWIR - wlRED)))', {
            'NIR': image.select(REDEDGE2), # red edge
            'RED': image.select(RED),
            'SWIR': image.select(NIR2), # narrow NIR band
            'wlNIR': 740,  # midpoint wavelength of red edge band in nm
            'wlRED': 665, # midpoint wavelength of RED band in nm
            'wlSWIR': 865,  # midpoint wavelength of narrow NIR band in nm
        }).rename('AFAI')
        return image.addBands(afai)

    # Calculate SEI - Seaweed Enhancing Index
    # Siddiqui et al, 2019, https:#www.mdpi.com/2072-4292/11/12/1434
    def addSEI(image):
        sei = image.normalizedDifference([NIR, SWIR1]).rename('SEI')
        return image.addBands(sei)

    # Sentinel Water Mask
    # Marta Milczarek et al. 2017
    # http:#eoscience.esa.int/landtraining2017/files/posters/MILCZAREK.pdf
    def addSWM(image):
        swm = image.expression(
            '(BLUE + GREEN) / (NIR + SWIR)',{
            'BLUE' : image.select(BLUE),
            'GREEN' : image.select(GREEN),
            'NIR' : image.select(NIR),
            'SWIR' : image.select(SWIR1)
        }).rename('SWM')
        return image.addBands(swm)

    # Define a function to print metadata column names and datatypes. This function
    # is intended to be applied by the `evaluate` method which provides the
    # function a client-side dictionary allowing the 'columns' object of the
    # feature collection metadata to be subset by dot notation or bracket notation
    # (`tableMetadata['columns']`).
    def getCols(tableMetadata):
        print(tableMetadata.columns)

    #-------- Calculate all INDICES on IMAGES -----------------------
    def addIndices(image):
        imageIdx = addNDVI(image)
        # imageIdx = addSAVI(imageIdx)
        imageIdx = addFAI(imageIdx)
        # imageIdx = addAFAI(imageIdx)
        imageIdx = addSEI(imageIdx)
        imageIdx = addSWM(imageIdx)
        return imageIdx

    #************************* END INDEX & CLOUD MASKING Functions *************************

    # ******************** Sentinel-2 IMAGE Selection, Masking, & Calculations *****************************

    # --------------- Annual S-2 Collections ---------------------------------
    s2 = ee.ImageCollection(s2_source) \
        .filterBounds(QR_multipoint) \
        .filterDate(annual_startdate, annual_enddate) \
        .select(S2bands)

    s2Clouds = ee.ImageCollection(s2_clouds_source)\
        .filterBounds(QR_multipoint)  \
        .filterDate(annual_startdate, annual_enddate)

    # Some outputs, like mosaic, end up with default projection - want to keep source
    # https:#developers.google.com/earth-engine/guides/projections#the-default-projection
    source_projection = s2.first().select('B2').projection()
    # print('Source Projection', source_projection)

    # Combine S2 with cloud probability by ID
    s2_wCloudProb = s2.combine(s2Clouds)
    # print('S2 Collection w/Cloud Prob:', s2_wCloudProb)

    # Scale spectral bands and copy other bands to new image
    s2_wCloudProb = s2_wCloudProb.map(scaleBands)
    # print('Scaled', s2_wCloudProb)

    # Calculate Indices for all images
    s2_wCloudProb = s2_wCloudProb.map(addIndices)
    # print('S2 Collection Annual: ', s2_wCloudProb)

    # Mask Clouds
    s2CloudMasked = ee.ImageCollection(s2_wCloudProb).map(maskCloudsProb)
    s2CloudMasked = s2CloudMasked.map(maskCloudsQA)

    # Images that show where clouds were masked - set to -1 value
    def cloudsBinary(image):
        clouds = image.select('probability').unmask(-1).lt(0).rename('clouds').copyProperties(image, ['system:time_start',
                                                                                                      'system:time_end',
                                                                                                      'system:footprint'])
        clouds = ee.Image(clouds).selfMask()
        return clouds

    s2CloudsOnly = s2CloudMasked.map(cloudsBinary)
    # print('Clouds Binary Collection', s2CloudsOnly.getInfo())

    # Add Annual NDVI summary bands
    # Apply NDVI Reducers to full time series
    # These bands end up as default projection (4326)
    # https:#developers.google.com/earth-engine/guides/ic_reducing
    # NDVImean = s2CloudMasked.select(NDVI).reduce(ee.Reducer.mean()) # .mean() # the shortcut names it as NDVI, without suffix
    NDVImedian = s2CloudMasked.select(NDVI).reduce(ee.Reducer.median())  # .median()
    # NDVIstdev = s2CloudMasked.select(NDVI).reduce(ee.Reducer.stdDev())
    NDVIminmax = s2CloudMasked.select(NDVI).reduce(ee.Reducer.minMax())
    summary_bands = ee.List([NDVImedian.bandNames(), NDVIminmax.bandNames()]).flatten()
    # print("Summary Band Names", summary_bands.getInfo())

    # Create Multi-Band Image from the single band NDVI summary images
    def addSummaryBands(image):
        # Return the image with the added bands.
        return image.addBands([NDVImedian, NDVIminmax])

    s2CloudMasked = s2CloudMasked.map(addSummaryBands)
    # print('S2 Cloud Masked Collection Annual: ', s2CloudMasked.getInfo())

    # -- Add NDVI difference band(s)
    def addNDVIdmed(image):
        ndvidmed = image.select('NDVI').subtract(image.select('NDVI_median')).rename(['NDVI_dmed'])
        return image.addBands(ndvidmed)

    s2CloudMasked = s2CloudMasked.map(addNDVIdmed)
    # print('S2 Cloud Masked Collection Annual with NDVI diff: ', s2CloudMasked.getInfo())

    # -------- Mask image to to areas of low elevation, NDVI > 0 and non-water

    # # Clip SRTM data to region and mask to elevations less than 10m
    srtmClip = SRTM.clip(QR_boundbox)
    elevationMask = SRTM.lt(elevation_threshold)

    def maskImage(image):
        # Use the NDVI and SWM to create image masks
        NDVIMask = image.select('NDVI').gt(ndvi_threshold)
        SWMMask = image.select('SWM').lt(swm_threshold)
        # Apply the NDVI, water, and elevation masks
        masked = (image
            .updateMask(NDVIMask)
            .updateMask(SWMMask)
            .updateMask(elevationMask)
                  )
        return masked

    s2AllMasked = s2CloudMasked.map(maskImage)
    # print('S2 All Masked Collection Annual: ', s2AllMasked.first().getInfo())

    # ******************** END Sentinel-2 IMAGE Selection, Masking, & Calculations *****************************

    # ******************** Select Single Date  *****************************

    #  Image Collections from a single date
    s2_1date = s2_wCloudProb.filterDate(image_date, image_date.advance(1, 'day'))
    s2_cloudmasked_1date = s2CloudMasked.filterDate(image_date, image_date.advance(1, 'day'))
    s2_allmasked_1date = s2AllMasked.filterDate(image_date, image_date.advance(1, 'day'))
    s2_clouds_1date = s2CloudsOnly.filterDate(image_date, image_date.advance(1, 'day'))
    # print('Cloud Masked Image Collection for ' + image_date_string, s2sr_cloudmasked_1date.first().getInfo())

    # *********************** CLASSIFICATION ************************************

    # Classify the fully masked image(s) using the Random Forest model
    ###################################################################

    def classifyImage(image):
        classifiedrf = image.select(bands_model).classify(classifier)  # .classify applies the Random Forest
        # To reduce noise, create a mask to mask unconnected pixels
        pixelcount = classifiedrf.connectedPixelCount(100,False)  # Create an image that shows the number of pixels each pixel is connected to
        countmask = pixelcount.select(0).gt(25)  # filter out all pixels connected to 4 or less
        # Mask the results to only display sargassum extent  (which is lc_code and classification = 0)
        classMask = classifiedrf.select('classification').eq(0)
        classed = classifiedrf.updateMask(classMask).updateMask(countmask)  # Returns only Sargassum with connected pixel filter
        return classed

    print('Classifying image.......')
    classified_collection = s2_allmasked_1date.map(classifyImage)
    classed = classified_collection.mosaic()
    # print("Classified Sargassum Collection", classified_collection.getInfo())

    # *************** Combine Sargassum Presence w/Absence & No Data ************************************

    # Region that were run through Classifier
    def getClassedArea(image):
        return image.select(['B2'],['classed_area']).gte(0)

    classed_area_collection = s2_allmasked_1date.map(getClassedArea)
    # print('Classified Area', classed_area_collection.first().getInfo())
    # print('Clouds only', s2sr_clouds_1date.first().getInfo())

    # Merge sargassum, classified area, and clouds into single collection using ID
    # combined_collection = classified_collection.combine(s2sr_clouds_1date).combine(classed_area_collection)
    print('Combining collections....')
    combined_collection = s2_clouds_1date.combine(classified_collection).combine(classed_area_collection)
    print('Combined', combined_collection.first().getInfo())

    # Merge  individual bands (presence/absence/no data) into a single band (sargassum)
    # no data (clouds) = -1
    # absent (classified region) = 0
    # present = 1
    def mergeImages(image):
        image_geometry = image.geometry()
        image_prj = image.select('clouds').projection()  #.crs()
        image_date = image.id().slice(0,8)
        image_tile = image.id().slice(32,38)
        merged = ee.Image(ee.ImageCollection([ee.Image(-1).int().updateMask(image.select('clouds').eq(1)),
                                      ee.Image(0).int().updateMask(image.select('classed_area').eq(1)),
                                      ee.Image(1).int().updateMask(image.select('classification').eq(0))]).mosaic()\
            .select(['constant'],['sargassum'])\
            .setDefaultProjection(image_prj) \
            .clipToBoundsAndScale(**{'geometry': image_geometry}) \
            .clipToCollection(nearshore_mask) \
            .copyProperties(image, ['system:time_start', 'system:time_end'])\
            .setMulti({'image_date': image_date, 'image_tile': image_tile}))
        merged = merged.unmask(-9999)
        return merged

    print('Merging images....')
    merged_collection = combined_collection.map(mergeImages)

    # Check some projection and other info
    print('Projection:', combined_collection.first().select('clouds').projection().getInfo())
    print('Scale:', combined_collection.first().select('clouds').projection().nominalScale().getInfo())
    print('Merged', merged_collection.first().getInfo())
    print('Merged size', merged_collection.size().getInfo())

    # # Single date mosaic  --- ONly need this for Accuracy Assessment
    # print('Mosaicking collection....')
    # image_date = merged_collection.first().get('image_date')
    # image_prj = merged_collection.first().select('sargassum').projection()
    # # print(image_date.getInfo())
    # mosaic = merged_collection.mosaic().setDefaultProjection(image_prj).set('image_date', image_date)
    # # print(mosaic.getInfo())
    # # Clip mosaic to nearshore mask
    # # print('Clipping mosaic.....')
    # # Already clipped individual images with nearshore mask, so don't need to do it here anymore
    # # mosaic_nearshore = mosaic.clipToCollection(nearshore_mask) #.setDefaultProjection(image_prj)
    # mosaic_nearshore = mosaic
    # print(mosaic_nearshore.getInfo())

    # print(nearshore_mask.geometry().getInfo())

    # ## Accuracy Assessment Random Samples  -- this is now down in ee_sargassum_aa.py7
    # print('Creating AA points..')
    # aaPoints = mosaic_nearshore.stratifiedSample(
    #     numPoints=100,
    #     classBand='sargassum',
    #     projection=image_prj,
    #     scale=10,
    #     region=nearshore_mask.geometry(), #.getInfo()['coordinates'],
    #     dropNulls=False,
    #     geometries=True
    # )
    # print('AA points', aaPoints.size().getInfo())
    # print('AA Points', aaPoints.first().getInfo())
    # Get User memory limit error when try to print these  or Export!

    # ******************** Export *****************************

    # Export the collection of classified image tiles
    geemap.ee_export_image_collection_to_drive(merged_collection, folder=output_folder, scale=10)

    ## Export Classified / clipped mosaic to Asset
    # output_image = 'classclipped_' + 'sr_' + image_date.getInfo()  # Surface Reflectance
    # # output_image = 'classclipped_' + 'toa_' + image_date.getInfo() + '_v3'  # Top of Atmosphere
    # assetid = asset_location + output_image
    # task = ee.batch.Export.image.toAsset(image=mosaic_nearshore,
    #                                      description=output_image,
    #                                      assetId=assetid,
    #                                      scale=10,
    #                                      region=QR_boundbox,
    #                                      maxPixels=1.0E13)
    # task.start()

    # # Export the classified clipped mosaic to Drive
    # output_image = 'classclipped_' + image_date.getInfo()
    # task = ee.batch.Export.image.toDrive(image=mosaic_nearshore,
    #                                      description=output_image,
    #                                      folder=output_folder,
    #                                      scale=10,
    #                                      region=QR_boundbox,
    #                                      maxPixels=1.0E13)
    # task.start()



# # ******************** Visualization *****************************
#
# rgbVisReflectance = {
#   'min': 0.0,
#   'max': 0.25,
#   'bands': [RED, GREEN, BLUE],
# }
# cirVisReflectance = {
#   'min': 0.0,
#   'max': 0.25,
#   'bands': [NIR, RED, GREEN],
# }
#
# Map.addLayer(s2sr_1date, cirVisReflectance, "S2 CIR - " + image_date_string, false)
# Map.addLayer(s2sr_1date, rgbVisReflectance, "S2 RGB - " + image_date_string, false)
#
# Map.addLayer(s2sr_cloudmasked_1date, cirVisReflectance, "S2 cloud masked CIR - " + image_date_string, true)
# Map.addLayer(s2sr_allmasked_1date, cirVisReflectance, "S2 all masked CIR - " + image_date_string, true)
#
# # print('Clouds Only', s2sr_clouds_1date)
# Map.addLayer(s2sr_clouds_1date, {}, 'Clouds Only')
#
# Map.addLayer(merged_collection.mosaic(), {'min':-1, 'max':1, 'palette': ["white", "blue", "pink"]}, 'Merged')
# Map.addLayer(combined_collection, {}, 'Combined Collection')
#
# Map.addLayer(classes, {}, 'Training Sites', false)
#
# #-- Classification
# Map.addLayer (classed, {min: 1, max: 1, palette:'fb04ff'}, 'Sargassum RF classified - '  + image_date_string)  # #fb04ff=pink

