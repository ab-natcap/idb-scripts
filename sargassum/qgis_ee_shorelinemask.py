""" qgis_ee_shorelinemask.py

Author: Allison Bailey
Date: 2021-03-22

This script is for use in QGIS to display false color S-2 image mosaics from GEE
"""

import ee
from ee_plugin import Map

# POint locations for QR S-2 Tiles, 16QDJ, 16QEJ, 16QDH, 16QEH, 16QDG, 16QDF
QR_multipoint = ee.Geometry.MultiPoint([[-87.4, 21.2],[-86.6, 21.2],[-87.4, 20.3],[-86.6, 20.3],[-87.4, 19.3],[-87.4, 18.3]])
S2bands = ee.List(['B2','B3','B4','B8'])

# Test Dates
multidateFilter = ee.Filter.Or(ee.Filter.date('2019-02-26','2019-02-27'),ee.Filter.date('2019-04-02','2019-04-03'),ee.Filter.date('2019-05-07','2019-05-08'),ee.Filter.date('2019-06-26','2019-06-27'),ee.Filter.date('2019-09-14','2019-09-15'),ee.Filter.date('2019-11-18','2019-11-19'),ee.Filter.date('2019-12-03','2019-12-04'))

# # Add individual dates here
# start_date = '2016-04-27'
# end_date = '2016-04-28'
# multidateFilter = ee.Filter.date(start_date,end_date)

s2sr = ee.ImageCollection('COPERNICUS/S2').filterBounds(QR_multipoint).filter(multidateFilter).select(S2bands)

# Add simple date and tile string prior to mosaic
def addProps(image):
    image_date=image.id().slice(0,8)
    image_tile=image.id().slice(32,38)
    return image.setMulti({'image_date': image_date, 'image_tile':image_tile})

s2sr_props = s2sr.map(addProps)

# Get list of unique dates in the collection
unique_dates = s2sr_props.aggregate_histogram('image_date').keys()
print(unique_dates.getInfo())

# Mosaic the images using the date string
def mosaicS2(date):
    col = s2sr_props.filterMetadata('image_date',"equals",date)
    return col.mosaic().set('image_date',date)

s2sr_mosaic = ee.ImageCollection(unique_dates.map(mosaicS2))


# - Visualization
BLUE = 'B2'
GREEN = 'B3'
RED = 'B4' 
NIR = 'B8'

cirVis = {
  'min': 0,
  'max': 2500,
  'bands': [NIR, RED, GREEN],
}

#*********** Classified Mosaics
colLength = s2sr_mosaic.size().getInfo()
listOfImages = s2sr_mosaic.toList(colLength)

for i in range(0, colLength):
    image = ee.Image(listOfImages.get(i))
    image_date = image.get('image_date').getInfo()
    Map.addLayer(image, cirVis, 'S2 CIR ' + image_date, False)


# # ********  Count of Sargassum presence

# classified_count = ee.Image("projects/ee-abnatcap/assets/sargassum/Sargassum2019_count")
# countviz = {
#   'min':1,
#   'max':7,
#   'palette': ['fef0d9', 'fdd49e', 'fdbb84', 'fc8d59', 'ef6548', 'd7301f', '990000'] # orange-y
#   # palette: ['feebe2', 'fcc5c0', 'fa9fb5', 'f768a1', 'dd3497', 'ae017e', '7a0177']  # pink-y
#   # palette: ['f2f0f7','dadaeb', 'bcbddc', '9e9ac8', '807dba', '6a51a3', '4a1486'] # purple
# }
# Map.addLayer(classified_count, countviz, 'Sargassum 2019 Count', False)