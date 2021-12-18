""" s2_sargassum_persistence.py

Author: Allison Bailey
Date: 2021-12-17

Generate Rasters that show the persistence of sargassum across dates
Heavily relied upon
https://www.earthdatascience.org/courses/use-data-open-source-python/intro-raster-data-python/raster-data-processing/classify-plot-raster-data-in-python/
"""

import os
import glob
import numpy as np
import xarray as xr
import rioxarray as rxr
import numpy as np

raster_dir = '/Users/arbailey/Google Drive/My Drive/sargassum/s2toa_classified_v1'

# Use the rasters that have all values assigned,
# 1=sargassum present, 0=absent, -1=no data (clouds),
# -9999=pre-masked non-sargassum pixels (deepwater, uplands) --> so reclass to 0
rasters = [r for r in glob.glob(os.path.join(raster_dir,"*mosaic_nd0.vrt"))]
print(rasters)
print(len(rasters))

# test set
rasters = ['/Users/arbailey/Google Drive/My Drive/sargassum/s2toa_classified_v1/20190211T161411_mosaic_nd0.vrt']

for r in rasters:
    allclasses = rxr.open_rasterio(r).squeeze()
    print(type(allclasses))
    print("The CRS for this data is:", allclasses.rio.crs)
    print("The spatial extent of this data is: ", allclasses.rio.bounds())
    print("The shape of this data is:", allclasses.shape)
    print("The no data value is:", allclasses.rio.nodata)
    # print("the minimum raster value is: ", np.nanmin(allclasses.values))
    # print("the maximum raster value is: ", np.nanmax(allclasses.values))
    present = allclasses.where(allclasses == 1)
    # intermediate = allclasses.where(allclasses == -9999, 0) #, 0, allclasses.all())  #, x=0, y=allclasses)
    intermediate = allclasses.where(allclasses != -1)  #, 0, allclasses.all())  #, x=0, y=allclasses)

    print(present)
    print(np.nanmin(present.values))
    print(np.nanmax(present.values))

    print(intermediate)
    print(np.nanmin(intermediate.values))
    print(np.nanmax(intermediate.values))

    class_bins = [1]

    sargassum = xr.apply_ufunc(np.digitize, intermediate, class_bins)
    print(sargassum)
    print(np.nanmin(sargassum.values))
    print(np.nanmax(sargassum.values))
