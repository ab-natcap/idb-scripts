""" s2_sargassum_persistence.py

Author: Allison Bailey
Date: 2021-12-17

Generate Rasters that show the persistence of sargassum across dates

"""

import os
import glob
import xarray as xr
import rioxarray as rxr
import numpy as np
import pygeoprocessing as pygeo
from osgeo import gdal
import time


def persist_rxr():
    # Raster source directory and data
    raster_dir = '/Users/arbailey/Google Drive/My Drive/sargassum/s2toa_classified_v1'

    # Use the rasters that have all values assigned,
    # 1=sargassum present, 0=absent, -1=no data (clouds),
    # -9999=pre-masked non-sargassum pixels (deepwater, uplands) --> so reclass to 0
    rasters = [r for r in glob.glob(os.path.join(raster_dir,"*mosaic_nd0.vrt"))]
    rasters.sort()

    # test set
    rasters = rasters[0:3]
    print("Raster list:", rasters)
    print("Count of input rasters ", len(rasters))

    # Relcass and sum rasters for persistence, using rioxarray approach -- currently runs out of memory...
    # Heavily relied upon
    # https://www.earthdatascience.org/courses/use-data-open-source-python/intro-raster-data-python/raster-data-processing/classify-plot-raster-data-in-python/
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

        # Try freeing memory by removing unneeded xarrays  -- didn't solve problem
        del allclasses
        del intermediate

    print(len(reclassed_rasters))
    persistence = reclassed_rasters[0]  # first raster is used to initialize
    # then sum the rest, one by oen
    for rast in reclassed_rasters[1:]:
        persistence += rast
    print(persistence)
    print("The CRS for this data is:", persistence.rio.crs)
    print("The spatial extent of this data is: ", persistence.rio.bounds())
    print("The shape of this data is:", persistence.shape)
    print("The no data value is:", persistence.rio.nodata)
    print("the minimum raster value is: ", np.nanmin(persistence.values))
    print("the maximum raster value is: ", np.nanmax(persistence.values))

    # Export summed raster
    persistence_path = os.path.join(raster_dir, "S2_sargassum_persistbypixel.tif")
    print("Exporting data to: ", persistence_path)
    persistence.rio.to_raster(persistence_path, dtype=np.uint8)
    # Error when trying to export:  TypeError: invalid dtype: 'int64'

    # When running all rasters (107, After 36 rasters, got this error:
    # Process finished with exit code 137 (interrupted by signal 9: SIGKILL) -- memory error


def persist_pygeo():
    start_time = time.time()
    source_dir = '/Users/arbailey/Google Drive/My Drive/sargassum/s2toa_classified_v1'
    out_dir = '/Users/arbailey/Google Drive/My Drive/sargassum/paper2022/data/source/s2qr_sargassum' # Remote
    out_dir = '/Users/arbailey/natcap/idb/data/work/sargassum/s2qr_sargassum'  # Local

    # Use the rasters that have all values assigned,
    # 1=sargassum present, 0=absent, -1=no data (clouds),
    # -9999=pre-masked non-sargassum pixels (deepwater, uplands) --> so reclass to 0
    in_rasters_path = [r for r in glob.glob(os.path.join(source_dir, "*mosaic_nd0.vrt"))]
    # in_rasters_path = in_rasters_path[0:2]
    in_rasters_path.sort()
    # in_rasters = [os.path.basename(r) for r in in_rasters_path]
    print(len(in_rasters_path), " rasters to reclassify")


    # Value map for reclassifying input rasters
    sargassum_vm = {
        -9999: 0,
        -1: -1,
        0: 0,
        1: 1
    }

    for in_path in in_rasters_path:
        in_raster_noext = os.path.splitext(os.path.basename(in_path))[0]
        image_date = in_raster_noext.split("_")[0]
        out_raster = f"s2qr_{image_date}_sargassum.tif"
        reclass_path = os.path.join(out_dir,out_raster)

        raster_reclass(in_path,reclass_path,sargassum_vm)

    print('ran in %.2fs' % (time.time() - start_time))

def raster_reclass(source_path, reclassed_path, value_map):
    """

    :param source_path: input raster full path
    :param reclassed_path: output (reclassified)
    :param value_map: value map for the reclassification
    :return:
    """
    print("Reclassifying {0} to {1}".format(source_path, reclassed_path))

    pygeo.geoprocessing.reclassify_raster(base_raster_path_band=(source_path, 1),
                                          target_raster_path=(reclassed_path),
                                          value_map=value_map,
                                          target_datatype=gdal.GDT_Int16,
                                          target_nodata=-1,
                                          )



if __name__ == '__main__':

    # Run Persistence Calcs with Rioxarray approach   -- ran out of memory
    # persist_rxr(rasters)

    # Run Persistence Calcs with Pygeoprocessing approach
    persist_pygeo()




