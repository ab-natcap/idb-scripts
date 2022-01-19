""" s2_sargassum_metrics.py

Author: Allison Bailey
Date: 2022-01-14

Calculate spatial and temporal metrics for Sentinel-2 classified sargassum images for Quintana Roo

Assumes the source rasters are for a single date, are spatially aligned and have the following values:
1 = Sargassum present
0 = Sargassum absent
-1 = No Data (clouds)

"""

import os
import glob
import rioxarray as rxr
import numpy as np
import pygeoprocessing as pygeo
from osgeo import gdal
import geopandas as gpd
from rasterstats import zonal_stats
import time

TARGET_NODATA = -1
TARGET_DATATYPE = gdal.GDT_Int16


def calc_metrics(in_path_list, out_dir, startdate, enddate):
    """ Main function to calculate a single persistence raster for a specified date range
        Assuming the input rasters have the following values
        Sargassum present: 1
        Sargassum absent: 0
        no data: -1
            Args:
                raster_path_list (list): list of strings of source raster file paths for metrics
                out_dir (string): directory location on disk to save outputs
                startdate: earliest date of interest (that has existing classified raster) YYYYMMDD
                enddate: latest date of interest YYYYMMDD
            Returns:
                Nothing
            """
    # Subset the raster list to match the date range
    subset_path_list = subset_list_by_daterange(in_path_list, startdate, enddate)
    # print(subset_path_list)
    raster_count = len(subset_path_list)

    # Output rasters
    sum_raster_path = os.path.join(out_dir, f'sargassum_presentcnt_by_pixel_{startdate}_{enddate}.tif')
    nodata_count_raster_path = os.path.join(out_dir, f'nodata_count_by_pixel_{startdate}_{enddate}.tif')
    persistence_raster_path = os.path.join(out_dir, f's2qr_sargassum_persistpct_{startdate}_{enddate}.tif')

    # Calculate a per-pixel sum of sargassum presence/absence across time series
    print("Creating sargassum presence count raster......")
    # sum_by_pixel(subset_path_list, sum_raster_path)
    print("Sum Raster: ", sum_raster_path)

    # Calculate a per-pixel count of no data occurrences
    print("Creating no data count raster......")
    # nodata_count_by_pixel(subset_path_list, nodata_count_raster_path)
    print("No Data Raster: ", nodata_count_raster_path)

    # Calculate persistence raster from sargassum presence and no data count rasters
    print("Creating sargassum persistence raster........")
    # persistence(sum_raster_path, nodata_count_raster_path, raster_count, persistence_raster_path)
    print("Persistence Raster: ", persistence_raster_path)

    # Zonal Stats by shoreline segment (within 100m) for persistence and area
    segment_poly_gpkg = '/Users/arbailey/Google Drive/My Drive/sargassum/paper2022/data/work/os2022.gpkg'
    segment_poly_layer = 'shoreQR_5km_segments_buff100m'
    persistence_layer = f's2qr_persistence_{startdate}_{enddate}'
    area_layer = f's2qr_area_{startdate}_{enddate}'

    print("Calculating persistence zonal stats")
    # persist_by_segment(persistence_raster_path, segment_poly_gpkg, segment_poly_layer, persistence_layer)

    print("Thresholding sargassum present count raster")
    threshold = 4  # Count of sargassum detections must be greater than this number
    threshhold_raster_path = os.path.join(out_dir, f'sargassum_presentcnt_gt{threshold}_{startdate}_{enddate}.tif')
    threshold_raster(sum_raster_path, threshhold_raster_path, threshold)

    print("Calculating sargassum area zonal stats")
    area_by_segment(threshhold_raster_path,  segment_poly_gpkg, segment_poly_layer, area_layer)



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
        sum_result = np.full(arrays[0].shape, 0, dtype=np.int16)
        for array in arrays:
            valid_mask = ~np.isclose(array, TARGET_NODATA)
            sum_result[valid_mask] = sum_result[valid_mask] + array[valid_mask]

        return np.where(sum_result == 0, TARGET_NODATA, sum_result)

    # raster calculate expects a list of (raster_path, band) tuples
    raster_path_band_list = [(raster_path, 1) for raster_path in raster_path_list]
    pygeo.raster_calculator(
        raster_path_band_list, sum_op, sum_raster_path, TARGET_DATATYPE,
        TARGET_NODATA)


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
        nodata_count_result = np.full(arrays[0].shape, 0, dtype=np.int16)
        for array in arrays:
            nodata_mask = np.isclose(array, TARGET_NODATA)
            nodata_count_result[nodata_mask] = nodata_count_result[nodata_mask] + 1

        return np.where(
            nodata_count_result == 0, TARGET_NODATA, nodata_count_result)

    # raster calculate expects a list of (raster_path, band) tuples
    raster_path_band_list = [(raster_path, 1) for raster_path in raster_path_list]
    pygeo.raster_calculator(
        raster_path_band_list, nodata_count_op, nodata_count_raster_path,
        TARGET_DATATYPE, TARGET_NODATA)


def persistence(sarg_sum_raster, nodata_sum_raster, raster_count, persist_raster):
    # Open input rasters -- sargassum occurrence count and no data count
    sarg_occur = rxr.open_rasterio(sarg_sum_raster, masked=True).squeeze()
    nodata_occur = rxr.open_rasterio(nodata_sum_raster, masked=True).squeeze()

    # Calculate persistence as % occurrence over valid observations (removing no data values)
    persist = (sarg_occur / (raster_count - nodata_occur)) * 100

    print("The CRS for this data is:", persist.rio.crs)
    print("The spatial extent of this data is: ", persist.rio.bounds())
    print("The shape of this data is:", persist.shape)
    print("The no data value is:", persist.rio.nodata)
    print("The encoded no data value is:", persist.rio.encoded_nodata)
    print("the minimum raster value is: ", np.nanmin(persist.values))
    print("the maximum raster value is: ", np.nanmax(persist.values))

    # Export
    print("Exporting data to: ", persist_raster)
    persist.rio.write_nodata(TARGET_NODATA, inplace=True)  # Set no data value for output
    persist.rio.to_raster(persist_raster, dtype=np.float32)

    # Calculate Raster Stats
    os.system('gdalinfo -stats ' + '"' + persist_raster + '"')


def persist_by_segment(persist_raster, gpkg, segment_layer, persistence_layer):
    # Calc Zonal Stats for 10m S2 persistence raster using buffered (100m)s shoreline segments
    segment_polys = gpd.read_file(gpkg, layer=segment_layer)
    zs = zonal_stats(segment_polys, persist_raster,
                     geojson_out=True,
                     nodata=TARGET_NODATA,
                     prefix = 'pst',
                     stats=['median','mean','max','count']
                     )
    persist_gdf = gpd.GeoDataFrame.from_features(zs)
    print(persist_gdf.columns)
    # print(persist_gdf.head())
    persist_gdf.set_crs(segment_polys.crs, inplace=True)
    persist_gdf.to_file(gpkg, layer=persistence_layer, driver="GPKG")


def threshold_raster(count_raster, threshold_raster, threshold):
    # Threshold the count of occurrence raster by a minimum
    sarg_occur = rxr.open_rasterio(count_raster, masked=True).squeeze()
    above_threshold = sarg_occur.where(sarg_occur > threshold)

    # Original data
    print("The CRS for this data is:", sarg_occur.rio.crs)
    print("The spatial extent of this data is: ", sarg_occur.rio.bounds())
    print("The shape of this data is:", sarg_occur.shape)
    print("The no data value is:", sarg_occur.rio.nodata)
    print("The encoded no data value is:", sarg_occur.rio.encoded_nodata)
    print("the minimum raster value is: ", np.nanmin(sarg_occur.values))
    print("the maximum raster value is: ", np.nanmax(sarg_occur.values))

    # Thresholded
    print("The CRS for this data is:", above_threshold.rio.crs)
    print("The spatial extent of this data is: ", above_threshold.rio.bounds())
    print("The shape of this data is:", above_threshold.shape)
    print("The no data value is:", above_threshold.rio.nodata)
    print("The encoded no data value is:", above_threshold.rio.encoded_nodata)
    print("the minimum raster value is: ", np.nanmin(above_threshold.values))
    print("the maximum raster value is: ", np.nanmax(above_threshold.values))
    # print(above_threshold)

    # Export
    print("Exporting data to: ", threshold_raster)
    above_threshold.rio.write_nodata(TARGET_NODATA, encoded=True, inplace=True)  # Set no data value for output
    above_threshold.rio.to_raster(threshold_raster, dtype=np.int16)

    os.system('gdalinfo -stats ' + '"' + threshold_raster + '"')


def area_by_segment(occur_raster, gpkg, segment_layer, area_layer):
    # Calculate count (area) of sargassum detected pixels
    segment_polys = gpd.read_file(gpkg, layer=segment_layer)
    zs = zonal_stats(segment_polys, occur_raster,
                     geojson_out=True,
                     nodata=TARGET_NODATA,
                     prefix='pxl',
                     stats=['count']
                     )
    occur_gdf = gpd.GeoDataFrame.from_features(zs)
    occur_gdf.drop(columns=['Length'],inplace=True)
    # Multiply pixel count by per pixel area to get maximum area of Sargassum
    occur_gdf['s2area_m2'] = occur_gdf['pxlcount'] * 100
    print(occur_gdf.columns)
    # print(persist_gdf.head())
    occur_gdf.set_crs(segment_polys.crs, inplace=True)
    # Export to geopackage layer
    occur_gdf.to_file(gpkg, layer=area_layer, driver="GPKG")


if __name__ == '__main__':

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
    calc_metrics(raster_path_list, out_dir, '20160427', '20191228')
    # Persistence 2017 - 2019
    calc_metrics(raster_path_list, out_dir, '20170112', '20191228')
    # Persistence 2018 - 2019
    calc_metrics(raster_path_list, out_dir, '20180112', '20191228')
    # Persistence 2017
    calc_metrics(raster_path_list, out_dir, '20170112', '20171228')
    # Persistence 2018
    calc_metrics(raster_path_list, out_dir, '20180112', '20181208')
    # Persistence 2019
    calc_metrics(raster_path_list, out_dir, '20190112', '20191228')


