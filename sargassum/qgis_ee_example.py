import ee
from ee_plugin import Map

S2sr = ee.Image("projects/ee-abnatcap/assets/sargassum/S2_20190507_16QDH")
S2sr_cloudmasked = ee.Image("projects/ee-abnatcap/assets/sargassum/S2_20190507_16QDH_cloudmasked")
S2sr_allmasked = ee.Image("projects/ee-abnatcap/assets/sargassum/S2_20190507_16QDH_masked")
S2sr_lowsarg = ee.Image('COPERNICUS/S2_SR/20190914T160859_20190914T162103_T16QDH')

print(S2sr)
print(S2sr.getInfo())

  
# Relevant Bands B2=blue, B3=green, B4=red, B8=NIR, B11,B12=SWIR, QA60=cloud mask
# B5, B6, B7 = red Edge (20m), B8A = NIR narrow wavelength, 20m res
S2bands = ee.List(['B2','B3','B4','B5','B6','B7','B8','B8A','B11','B12','QA60'])
S2bands_spectral = ee.List(S2bands).remove('QA60')
BLUE = 'B2'  
GREEN = 'B3'
RED = 'B4' 
REDEDGE1 = 'B5'
REDEDGE2 = 'B6'
REDEDGE3 = 'B7'
NIR = 'B8'
NIR2 = 'B8A' 
SWIR1 = 'B11' 
SWIR2 = 'B12' 

cirVis = {
  'min': 0,
  'max': 2500,
  'bands': [NIR, RED, GREEN],
}

rgbVisReflectance = {
  'min': 0.0,
  'max': 0.25,
  'bands': [RED, GREEN, BLUE],
}
cirVisReflectance = {
  'min': 0.0,
  'max': 0.25,
  'bands': [NIR, RED, GREEN],
}
# Add S2 layer
Map.addLayer(S2sr, cirVisReflectance, "S2 CIR - 2019-05-07", False)
Map.addLayer(S2sr, rgbVisReflectance, "S2 RGB - 2019-05-07", False)
Map.addLayer(S2sr_cloudmasked, cirVisReflectance, "S2 Cloud Masked - 2019-05-07", False)
Map.addLayer(S2sr_allmasked, cirVisReflectance, "S2 All Masked - 2019-05-07", False)
Map.addLayer(S2sr_lowsarg, cirVis, "S2 CIR - 2019-09-14", False)

# Planet Scope imagery
image_date = ee.Date('2019-05-07')

PlanetScope_Collection = ee.ImageCollection("projects/ee-abnatcap/assets/PSScene4Band_MAR")
PS_201905_Collection = PlanetScope_Collection.filterDate(image_date, image_date.advance(2,'day')) 

PlanetRGBvis = {"opacity":1,"bands":["B3","B2","B1"],"min":405.79,"max":4499.71,"gamma":2.331}
PlanetCIRvis = {"opacity":1,"bands":["B4","B2","B3"],"min":405.79,"max":4499.71,"gamma":2.331}

Map.addLayer(PS_201905_Collection, PlanetRGBvis, "Planet RGB", False)
Map.addLayer(PS_201905_Collection, PlanetCIRvis, "Planet CIR", False)