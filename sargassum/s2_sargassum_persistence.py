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
rasters.sort()

# test set
# rasters = rasters[0:2]
# rasters = ['/Users/arbailey/Google Drive/My Drive/sargassum/s2toa_classified_v1/20190211T161411_mosaic_nd0.vrt']
print("Raster list:", rasters)
print("Count of input rasters ", len(rasters))

reclassed_rasters = []
for r in rasters:
    print(os.path.basename(r))
    # Open the raster and squeeze into two dimensions (ignore "band dimension which is 1)
    allclasses = rxr.open_rasterio(r).squeeze()  # squeeze removes the "band" dimension (which is 1)
    # print(type(allclasses))
    # print("The CRS for this data is:", allclasses.rio.crs)
    # print("The spatial extent of this data is: ", allclasses.rio.bounds())
    # print("The shape of this data is:", allclasses.shape)
    # print("The no data value is:", allclasses.rio.nodata)
    # print("the minimum raster value is: ", np.nanmin(allclasses.values))
    # print("the maximum raster value is: ", np.nanmax(allclasses.values))

    # # Raster of Sargassum present (=1)  -- This is just an example, used the logic for intermediate, below
    # present = allclasses.where(allclasses == 1)
    #
    # Raster of present/absent (1, 0, -9999 (pre-masked as not Sargassum, so equivalent to 0)
    intermediate = allclasses.where(allclasses != -1)  #, 0, allclasses.all())  #, x=0, y=allclasses)

    # Reclassify everything that isn't = 1 to zero
    # So, <1 becomes 0, >= 1 becomes 1
    class_bins = [1]
    sargassum = xr.apply_ufunc(np.digitize, intermediate, class_bins)
    # print("Info from reclassed Sargassum raster:")
    # print(sargassum)
    # print("Min value: ",np.nanmin(sargassum.values))
    # print("Max value: ",np.nanmax(sargassum.values))
    reclassed_rasters.append(sargassum)

print(len(reclassed_rasters))
