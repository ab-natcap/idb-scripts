""" srtm_mangrove_polygons.py

Author: Allison Bailey
Date: 2020-01-14

Vectorized the Masked SRTM grids and overlay with the mangrove polygons

Assumes all geographic data are in the same projection (currently EPSG 4326)

Examples of raster to poly:
https://gis.stackexchange.com/questions/295362/how-to-polygonize-raster-file-according-to-band-values
https://gis.stackexchange.com/questions/187877/how-to-polygonize-raster-to-shapely-polygons

"""

import os
import time
import datetime
import glob
import pprint
import rasterio
from rasterio import features
import geopandas as gpd
import multiprocessing


def time_elapsed(start_time):
    """

    :param start_time: Start time
    :return: current time - start time formatted as hours:minutes:seconds
    """
    te = time.time() - start_time
    # print(str(datetime.timedelta(seconds=te)))
    return str(datetime.timedelta(seconds=te))

def process_data(hgtgrid_file, mangrove_gdf, attribute):
    """

    :param hgtgrid_file: mangrove height estimate grid
    :param mangrove_gdf: mangrove boundary polygons as a GeoDataFrame
    :return:

    """
    # # From https://rasterio.readthedocs.io/en/stable/topics/features.html#extracting-shapes-of-raster-features
    # # Tuple of geometry and raster
    # #   -- Did not Use this section
    # #  Not sure advantages of using this versus the features.dataset_features
    # # Number of features returned is 51057 (more than features.dataset_features, 51048) -- not grouping contiguous cells?
    # with rasterio.open(hgtgrid_file) as src:
    #     height_np = src.read(1)
    #     shapes = features.shapes(height_np, transform=src.transform)
    # # pprint.pprint(next(shapes))

    #  See https://rasterio.readthedocs.io/en/stable/api/rasterio.features.html
    # Convert Rasters to polygons of same values using source raster CRS
    # The number of records returned for 'wam_hba_N21W087.tif' is 51048
    with rasterio.open(hgtgrid_file) as src:
        crs = src.crs
        feats = features.dataset_features(src, bidx=1, geographic=False)
        # Convert iterator to a list
        feats_list = list(feats)
    # pprint.pprint(feats_list[0])

    # Continue processing if there are features in the vectorized raster (some are all No Data grids)
    if len(feats_list):
        # Convert vectorized features list to a GeoDataFrame with CRS from source raster
        feats_gdf = gpd.GeoDataFrame.from_features(feats_list, crs=crs)
        # Rename raster value column to be more specific
        feats_gdf.rename(
            columns={'val': attribute},
            inplace=True
        )
        # Drop extraneous column (if it exists)
        feats_gdf.drop(columns=['filename'], errors='ignore', inplace=True)

        # Overlay Mangrove boundaries and raster height features
        # Result is original shapes of mangrove polys  with height attributes
        # This takes a few minutes
        start_time = time.time()
        height_intersect_gdf = gpd.overlay(mangrove_gdf, feats_gdf, how='intersection')
        execution_time = time_elapsed(start_time)
        print("Intersect time for {0}: {1}".format(hgtgrid_file, execution_time))

        # # Export GeoDataFrame to Shapefile
        tile_name = os.path.splitext(hgtgrid_file)[0]
        out_polygon_file = "{}_overlay.shp".format(tile_name)
        height_intersect_gdf.to_file(out_polygon_file)
        print(out_polygon_file)


def worker(work_queue, poly_gdf, attribute):

    for raster in iter(work_queue.get, 'STOP'):
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ', begin processing file ' + raster)
        process_data(raster, poly_gdf, attribute)
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ', finished processing file ' + raster)
        work_queue.task_done()
    work_queue.task_done()


def main(raster_list, mangrove_gdf, attribute):
    work_queue = multiprocessing.JoinableQueue()

    for raster in raster_list:
        work_queue.put(raster)

    # NUMBER_OF_PROCESSES = multiprocessing.cpu_count()
    # print(NUMBER_OF_PROCESSES)  # This returns 16 on my 8 core machine ??
    NUMBER_OF_PROCESSES = 1
    for _ in range(NUMBER_OF_PROCESSES):
        multiprocessing.Process(target=worker, args=[work_queue, mangrove_gdf, attribute]).start()

    for _ in range(NUMBER_OF_PROCESSES):
        work_queue.put('STOP')

    work_queue.join()


if __name__ == "__main__":
    #### ---- SETUP, get list of rasters and call main function ----------

    # Top level data directory
    data_dir = '/Users/arbailey/natcap/idb/data/work/mangroves'

    # Vector shapefile paths
    # World Atlas of Mangroves
    wam_path = os.path.join(data_dir, 'wam_Bahamas_MAR.shp')
    wam_prefix = 'wam'

    # Global Mangrove Watch
    gmw2016_path = os.path.join(data_dir, 'gmw2016_Bahamas_MAR.shp')
    gmw2016_prefix = 'gmw2016'

    # Load mangrove polygons
    wam_gdf = gpd.GeoDataFrame.from_file(wam_path)
    gmw2016_gdf = gpd.GeoDataFrame.from_file(gmw2016_path)

    # Working directory
    work_dir = os.path.join(data_dir, 'srtm')
    os.chdir(work_dir)

    hba_prefix = 'hba'
    hmax_prefix = 'hmax'
    hba_attribute = '{}_m'.format(hba_prefix)
    hmax_attribute = '{}_m'.format(hmax_prefix)

    wam_hmax_rasters = glob.glob("wam_hmax_*.tif")
    wam_hba_rasters = glob.glob("wam_hba_*.tif")
    gmw2016_hmax_rasters = glob.glob("gmw2016_hmax_*.tif")
    gmw2016_hba_rasters = glob.glob("gmw2016_hba_*.tif")

    # Testing subsets or missing tiles
    # input_rasters = ['wam_hba_N21W087.tif', 'wam_hba_N21W088.tif', 'wam_hba_N21W089.tif', 'wam_hba_N21W090.tif']
    # input_rasters = ['wam_hba_N21W087.tif']
    # main(input_rasters, wam_gdf, hba_attribute)
    # input_rasters = ['wam_hmax_N16W088.tif', 'wam_hmax_N24W080.tif', 'wam_hmax_N26W080.tif', 'wam_hmax_N22W076.tif']
    # main(input_rasters, wam_gdf, hmax_attribute)

    # These didn't complete in the original run -- seem to have significantly more polys than other tiles
    input_rasters = ['gmw2016_hba_N19W088.tif', 'gmw2016_hba_N20W091.tif']
    main(input_rasters, gmw2016_gdf, hba_attribute)
    input_rasters = ['gmw2016_hmax_N19W088.tif', 'gmw2016_hmax_N20W091.tif']
    main(input_rasters, gmw2016_gdf, hmax_attribute)

    #-- FINAL - Max Height and WAM
    # main(wam_hmax_rasters, wam_gdf, hmax_attribute)
    #
    # main(wam_hba_rasters, wam_gdf, hba_attribute)
    #
    # main(gmw2016_hmax_rasters, gmw2016_gdf, hmax_attribute)
    #
    # main(gmw2016_hba_rasters, gmw2016_gdf, hba_attribute)


