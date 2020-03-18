""" gliht_mangrove_overlay.py

Author: Allison Bailey
Date: 2020-03-13

Overlay G-LiHT and SRTM sampled points with mangrove extent and height layers
This is run after gliht_prep.py and gliht_srtm_sample.py

Assumes all data are in 4326 (lat/long WGS-84)

"""

import os
import numpy as np
import rasterio as rio
# import pandas as pd
import geopandas as gpd
# import fiona
# from shapely.geometry import box
from geofeather import to_geofeather, from_geofeather
import time
import datetime


def time_elapsed(start_time):
    """
    Calculate a string representation of  elapsed time given an input start time
    :param start_time: Start time
    :return: current time - start time formatted as hours:minutes:seconds
    """
    te = time.time() - start_time
    # print(str(datetime.timedelta(seconds=te)))
    return str(datetime.timedelta(seconds=te))


def mangrove_poly_to_gdf(source_path, mangrove_attribute):
    """

    Creates a geodataframe with a single attribute column for mangrove presence/absence
    Assumes the source polygons are only mangrove presence
    :param source_path: Path to the source vector data
    :param mangrove_attribute:  column name for the mangrove presence attribute
    :return:  Geodataframe with the single attribute for mangrove presence
    """

    gdf = gpd.read_file(source_path)
    gdf[mangrove_attribute] = 1
    gdf = gdf[[mangrove_attribute, 'geometry']]
    return gdf


def mangrove_join(pt_gdf, mangrove_gdf):
    """

    :param pt_gdf:  Points to get the mangrove attributes
    :param mangrove_gdf:  Geodataframe with the mangrove polygons and presence/absence attribute
    :return:  joined_gdf:  Point geodataframe with mangrove presence/absence attributes
    """

    # Join Attributes of mangrove polygons to master point layer
    start_time = time.time()
    print("Joining mangrove polys with points GDF")
    joined_gdf = gpd.sjoin(pt_gdf, mangrove_gdf, how="left")
    joined_gdf = joined_gdf.drop(columns='index_right')
    print("Joining execution time: {}".format(time_elapsed(start_time)))
    return joined_gdf

def point_coords(geom):
    """
    Return a single tuple with the x/y point coordinate for a GeoDataFrame geometry
    :param geom: input a geometry object (from GDF, for example
    :return: The first tuple in the list, which is a point
    """
    # Return a tuple with the x/y point coordinate for a GeoDataFrame geometry
    return list(geom.coords)[0] # Just get first tuple in list, since it's a point


def sample_raster(pt_gdf, raster_path, att):

    start_time = time.time()
    print("Sampling raster {} with points GDF".format(raster_path))

    # Get the point coordinate tuples from the Point Geodatafram
    pt_coords = pt_gdf.apply(lambda row: point_coords(row.geometry), axis=1)

    # Sample the raster with point coordinates
    with rio.open(raster_path) as rast:
        print(rast.meta)
        sample_gen = rast.sample(xy=pt_coords)
        # Convert generator to a list for appending to geodataframe
        # Conversion of generator to list crashes if points are not completely covered by the raster
        # So, incorporated previous step for clipping the points with the raster bounding box
        sample = list(sample_gen)

    # Append sampled values to copy of the Geodataframe
    pt_gdf_sampled = pt_gdf.copy()
    pt_gdf_sampled[att] = np.vstack(sample)
    print(pt_gdf_sampled)

    print("Sample execution time for {0}: {1}".format(raster_path, time_elapsed(start_time)))

    return pt_gdf_sampled


def make_unique_raster(in_raster_path, out_raster_path):
    """

    :param in_raster_path:
    :param out_raster_path:
    :return:
    """

    start_time = time.time()
    print("Creating a raster with unique cell IDS {}".format(out_raster_path))

    # Create an array with unique ID for each pixel
    with rio.open(in_raster_path) as src:
        rows, cols = src.shape
        raster_uniqueid_np = np.arange(rows * cols).reshape(rows, cols) + 1 # want to start at 1 and not zero for ids
        raster_unique_meta = src.meta

    # numpy datatype must match tiff output data type (?) - when I didn't do this I got errors
    raster_uniqueid_np = raster_uniqueid_np.astype('uint32')
    # Get metadata from source and apply to unique ID raster
    raster_unique_meta['dtype'] = rio.uint32  # change data type to hold all values
    raster_unique_meta['nodata'] = 0  # No data value
    raster_unique_meta['driver'] = 'GTiff'

    # Convert input raster to uniqueID raster
    with rio.open(out_raster_path, 'w', **raster_unique_meta) as dst:
        dst.write(raster_uniqueid_np, 1)

    print("Create Unique ID execution time for {0}: {1}".format(out_raster_path, time_elapsed(start_time)))


def main(tile, input_pt_feather):

    # Data Directories
    data_dir = '/Users/arbailey/natcap/idb/data/work/mangroves'
    work_dir = os.path.join(data_dir, 'yucatan')
    pt_data_source = os.path.join(work_dir, input_pt_feather)

    out_feather_path = os.path.join(work_dir, "gliht_srtm_mangroves_{}.feather".format(tile))

    # --- Mangrove Max Height raster
    hmax_source = os.path.join(data_dir, 'gmc_hmax95_bahamas_MAR.tif')
    hba_source = os.path.join(data_dir, 'gmc_hba95_bahamas_MAR.tif')

    #--- Load the G-LiHT/SRTM points
    print("Loading data from: {}".format(pt_data_source))
    start_time = time.time()
    gliht_pts = from_geofeather(os.path.join(work_dir, pt_data_source))
    print("Load time for {0}: {1}".format(pt_data_source, time_elapsed(start_time)))
    gliht_pts.drop(columns=['index'], inplace=True)
    print(gliht_pts.dtypes)
    print(gliht_pts)

    # Sample the Canopy Height rasters
    # Max Height - hmax95
    # gliht_pts = sample_raster(gliht_pts[0:100], hmax_source, 'hmax95')
    gliht_pts = sample_raster(gliht_pts, hmax_source, 'hmax95')
    print(gliht_pts.dtypes)
    print(gliht_pts)
    # Weighted Average Height - hba95
    gliht_pts = sample_raster(gliht_pts, hba_source, 'hba95')
    print(gliht_pts.dtypes)
    print(gliht_pts)

    # # Create unique index value for Canopy raster
    gmc_unique_source = os.path.join(work_dir, "gmc_uniqueid.tif")
    # make_unique_raster(hmax_source, gmc_unique_source)  # Takes 1:55:14.79
    #
    # Sample Unique ID raster
    gliht_pts = sample_raster(gliht_pts, gmc_unique_source, 'hmax_idx')
    # gliht_pts.reset_index(inplace=True)
    # gliht_pts.drop(columns=['index'], inplace=True)
    print(gliht_pts.dtypes)
    print(gliht_pts)

    # Add columns to show the tile and unique index plus tile
    gliht_pts['tile'] = tile
    gliht_pts['tile_hmaxidx'] = gliht_pts['tile'] + '_' + gliht_pts['hmax_idx'].astype(str)
    print(gliht_pts.dtypes)
    print(gliht_pts)

    # Mangrove Extent Vector shapefile paths to join to Points
    #-- World Atlas of Mangroves
    wam_path = os.path.join(data_dir, 'wam_Bahamas_MAR.shp')
    wam_att = 'wam'
    wam = mangrove_poly_to_gdf(wam_path, wam_att)
    print(wam)
    gliht_pts = mangrove_join(gliht_pts, wam)
    print(gliht_pts)

    #-- Global Mangrove Watch
    gmw2016_path = os.path.join(data_dir, 'gmw2016_Bahamas_MAR.shp')
    gmw2016_att = 'gmw2016'
    gmw2016 = mangrove_poly_to_gdf(gmw2016_path, gmw2016_att)
    print(gmw2016)
    gliht_pts = mangrove_join(gliht_pts, gmw2016)
    print(gliht_pts)

    # Global Mangrove Forests
    gmf_path = os.path.join(data_dir, 'gmf_bahamas_MAR.shp')
    gmf_att = 'gmf'
    gmf = mangrove_poly_to_gdf(gmf_path, gmf_att)
    print(gmf)
    gliht_pts = mangrove_join(gliht_pts, gmf)
    print(gliht_pts)

    # NAtCap Mangrove compilation for MAR region (Mex, Belize, Guatemala, Honduras)
    ncmar_path = os.path.join(data_dir, 'natcap_mangrovesV4_MAR.shp')
    ncmar_att = 'ncMAR'
    ncmar = mangrove_poly_to_gdf(ncmar_path, ncmar_att)
    print(ncmar)
    gliht_pts = mangrove_join(gliht_pts, ncmar)
    print(gliht_pts)

    print(gliht_pts.dtypes)
    print(gliht_pts.describe())

    # Export to GeoFeather format
    gliht_pts.reset_index(inplace=True)  # get an error from feather export if don't do this
    # ValueError: feather does not support serializing a non-default index for the index; you can .reset_index() to make the index into column(s)
    print(gliht_pts.dtypes)
    print("Exporting to Geofeather format")
    start_time = time.time()
    to_geofeather(gliht_pts, out_feather_path)
    print("Export execution time for {0}: {1}".format(out_feather_path, time_elapsed(start_time)))


#### ---- SETUP and call main function ----------

if __name__ == '__main__':

    # out_geopackage = 'gliht_yucatan.gpkg'

    # # ------ GLiHT AMIGACarb_Out_of_the_Yuc_GLAS_May2013 data --------------
    # # Single 1 degree tile for overlap area
    # ----- This takes ~ 3 hrs to run
    # yuceast_tile = 'N20W088'
    # gliht_pts_yuceast_feather = 'gliht_srtm_N20W088.feather'
    # main(yuceast_tile, gliht_pts_yuceast_feather)

    #  ------ GLiHT AMIGACarb_Yuc_Norte_GLAS_Apr2013  --------------------
    # Single 1 degree tile for overlap area
    # ----- This takes ~ 27 hrs to run
    yucwest_tile = 'N20W091'
    gliht_pts_yucwest_feather = 'gliht_srtm_N20W091.feather'
    main(yucwest_tile, gliht_pts_yucwest_feather)
