""" s2_sargassum_persistence.py

Author: Allison Bailey
Date: 2021-12-17

Generate Rasters that show the persistence of sargassum across dates

A bunch of these functions were experimental and did not necessarily work

Instead, did the preliminary alignment and reclassification in reclass_summ_and_nodata_count.py

Actual workflow replaced by s2_sargassum_metrics.py

"""

import os
import glob
import xarray as xr
import rioxarray as rxr
import numpy as np
import pygeoprocessing as pygeo
from osgeo import gdal
import time

TARGET_NODATA = -1
TARGET_DATATYPE = gdal.GDT_Int16

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
    # Create Sargassum Persistence Raster from individual dates classified as presence (1), absence (0) or no data (-1)
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

    # Reclassifiy the original rasters
    reclassed_rasters = []
    for in_path in in_rasters_path:
        in_raster_noext = os.path.splitext(os.path.basename(in_path))[0]
        image_date = in_raster_noext.split("_")[0]
        out_raster = f"s2qr_{image_date}_sargassum.tif"
        reclass_path = os.path.join(out_dir,out_raster)
        reclassed_rasters.append(reclass_path)

        # raster_reclass(in_path,reclass_path,sargassum_vm)

    print(reclassed_rasters)



    # Sum the reclassified rasters
    sum_rasters(reclassed_rasters)

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


def sum_rasters(rasters):
    """
    :param rasters: input list of rasters with full path
    :return:
    """
    for i, r in enumerate(rasters):
        print(os.path.basename(r))
        # Open the raster and squeeze into two dimensions (ignore "band dimension which is 1)
        # https://corteva.github.io/rioxarray/stable/getting_started/nodata_management.html#
        classed = rxr.open_rasterio(r, masked=True).squeeze()  # squeeze removes the "band" dimension (which is 1)
        if i == 0:
            summed = classed
            print("The CRS for this data is:", summed.rio.crs)
            print("The spatial extent of this data is: ", summed.rio.bounds())
            print("The shape of this data is:", summed.shape)
            print("The no data value is:", summed.rio.nodata)
            print("The encoded no data value is:", summed.rio.encoded_nodata)
            print("the minimum raster value is: ", np.nanmin(summed.values))
            print("the maximum raster value is: ", np.nanmax(summed.values))
        else:
            # https://corteva.github.io/rioxarray/stable/examples/reproject_match.html#Raster-Calculations
            try:
                summed += classed
            except: # xr.MergeError:
                # if problem merging due to unaligned rasters, do reproject match
                print("Doing projection match")
                print("The CRS for input data is:", classed.rio.crs)
                print("The spatial extent of input data is: ", classed.rio.bounds())
                print("The shape of input data is:", classed.shape)
                classed_reprjmatch = classed.rio.reproject_match(summed)
                summed += classed_reprjmatch

    print("The CRS for this data is:", summed.rio.crs)
    print("The spatial extent of this data is: ", summed.rio.bounds())
    print("The shape of this data is:", summed.shape)
    print("The no data value is:", summed.rio.nodata)
    print("The encoded no data value is:", summed.rio.encoded_nodata)
    print("the minimum raster value is: ", np.nanmin(summed.values))
    print("the maximum raster value is: ", np.nanmax(summed.values))


def subset_list_by_daterange(in_raster_path_list, startdate, enddate):
    """
    Subset the list of rasters in the input directory for a specific date range

    :param in_raster_path_list:
    :param startdate:
    :param enddate:
    :return: out_raster_path_list
    """

    # Sort the list and then get the indices for the start and end dates to slice the list
    in_raster_path_list.sort()
    startindex = [i for i,path in enumerate(in_raster_path_list) if startdate in path][0]
    endindex = [i for i,path in enumerate(in_raster_path_list) if enddate in path][0] + 1
    out_raster_path_list = in_raster_path_list[startindex:endindex]

    # Print input dates and output list length for QC
    print(f'Date Start: {startdate}  Date End: {enddate}')
    print(f"Number of subset rasters: {len(out_raster_path_list)}")

    return out_raster_path_list


def calc_persist(in_path_list, out_dir, startdate='20151119', enddate='20191228'):
    """ Calculate a single persistence raster, based on a list of rasters with the following classification
        Sargassum present: 1
        Sargassum absent: 0
        no data: -1
            Args:
                raster_path_list (list): list of strings of raster file paths to sum
                out_dir (string): directory location on disk to save sum raster
            Returns:
                sum_raster_path (string):  full path to sum raster
            """
    # Subset the raster list to match the date range
    subset_path_list = subset_list_by_daterange(in_path_list, startdate, enddate)
    # print(subset_path_list)

    # Calculate a per-pixel sum of sargassum presence/absence across time series
    sum_raster_path = os.path.join(out_dir, f'sargassum_presentcnt_by_pixel_{startdate}_{enddate}.tif')
    sum_by_pixel(subset_path_list, sum_raster_path)
    print("Sum Raster: ", sum_raster_path)

    # Calculate a per-pixel count of no data occurrences
    nodata_count_raster_path = os.path.join(out_dir, f'nodata_count_by_pixel_{startdate}_{enddate}.tif')
    nodata_count_by_pixel(subset_path_list, nodata_count_raster_path)
    print("No Data Raster: ", nodata_count_raster_path)


def sum_by_pixel(raster_path_list, sum_raster_path):
    """Pixel sum the rasters treating nodata values as zero.
        Args:
            raster_path_list (list): list of strings of raster file paths to sum
            sum_raster_path (string):  full path to sum raster
        Returns:
            Nothing
        """

    def sum_op(*arrays):
        """Computes the per pixel sum of the arrays.
        This operation treats nodata values as 0.
        Args:
            *arrays (list): a list of numpy arrays
        Returns:
            Per pixel sums.
        """
        sum_result = np.full(arrays[0].shape, 0, dtype=numpy.int16)
        for array in arrays:
            valid_mask = ~np.isclose(array, TARGET_NODATA)
            sum_result[valid_mask] = sum_result[valid_mask] + array[valid_mask]

        return np.where(sum_result == 0, TARGET_NODATA, sum_result)

    # raster calculate expects a list of (raster_path, band) tuples
    raster_path_band_list = [(raster_path, 1) for raster_path in raster_path_list]
    # pygeo.raster_calculator(
    #     raster_path_band_list, sum_op, sum_raster_path, TARGET_DATATYPE,
    #     TARGET_NODATA)



def nodata_count_by_pixel(raster_path_list, nodata_count_raster_path):
    """A nodata pixel count of rasters.
    Args:
        raster_path_list (list): list of strings of raster file paths
        out_dir (string): directory location on disk to save raster
    Returns:
        Nothing
    """


    def nodata_count_op(*arrays):
        """Computes the nodata count per pixel of the arrays.
        Args:
            *arrays (list): a list of numpy arrays
        Returns:
            Nodata counts.
        """
        nodata_count_result = numpy.full(arrays[0].shape, 0, dtype=numpy.int16)
        for array in arrays:
            nodata_mask = numpy.isclose(array, TARGET_NODATA)
            nodata_count_result[nodata_mask] = nodata_count_result[nodata_mask] + 1

        return numpy.where(
            nodata_count_result == 0, TARGET_NODATA, nodata_count_result)

    # raster calculate expects a list of (raster_path, band) tuples
    raster_path_band_list = [(raster_path, 1) for raster_path in raster_path_list]
    # pygeo.raster_calculator(
    #     raster_path_band_list, nodata_count_op, nodata_count_raster_path,
    #     TARGET_DATATYPE, TARGET_NODATA)



if __name__ == '__main__':

    # Run Persistence Calcs with Rioxarray approach   -- ran out of memory
    # persist_rxr(rasters)

    # Run Persistence Calcs with Pygeoprocessing approach # -- did most of this in reclass_sum_and_nodata_count.py script
    # persist_pygeo()


    # setup directories
    remote_base_dir = '/Users/arbailey/Google Drive/My Drive/sargassum/paper2022/data/source/s2qr_sargassum' # Remote
    local_base_dir = '/Users/arbailey/natcap/idb/data/work/sargassum/s2qr_sargassum'  # Local
    # base_dir = os.path.join('Users', 'arbailey', 'natcap', 'idb', 'data', 'work', 'sargassum', 's2qr_sargassum')
    base_dir = remote_base_dir
    source_dir = os.path.join(base_dir, 'mosaics_by_date')
    out_dir = base_dir

    # collect the raster paths from the source directory
    raster_path_list = [r for r in glob.glob(os.path.join(source_dir, "s2qr_*sargassum.tif"))]
    # print(raster_path_list)
    print(f"Number of source rasters: {len(raster_path_list)}")

    # Persistence 2016 - 2019
    calc_persist(raster_path_list, out_dir, '20160427', '20191228')




