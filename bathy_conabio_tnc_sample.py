""" bathy_conabio_tnc_sample.py

Author: Allison Bailey
Date: 2020-05-01

Sample SRTM (DEM) raster with G-LiHT points
This is run after gliht_prep.py

Assumes all data are in 4326 (lat/long WGS-84)

"""

import os
import numpy as np
import rasterio as rio
import geopandas as gpd
from shapely.geometry import box
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

def point_coords(geom):
    """
    Return a single tuple with the x/y point coordinate for a GeoDataFrame geometry
    :param geom: input a geometry object (from GDF, for example
    :return: The first tuple in the list, which is a point
    """
    # Return a tuple with the x/y point coordinate for a GeoDataFrame geometry
    return list(geom.coords)[0] # Just get first tuple in list, since it's a point


def clip_pts_with_raster(pt_gdf, raster_path):
    """
    Clip a geodataframe with a raster bounding box
    :param pt_gdf: Input Point Geodataframe to be clipped
    :param raster_path: path to raster to use for clipping box
    :return: clipped geodataframe
    """

    start_time = time.time()

    print("Clipping points GDF with raster: {}".format(raster_path))
    # Bounds of the points
    print("Point data bounds before clip {}".format(pt_gdf.geometry.total_bounds))

    # Get the raster bounding box and convert to a shapely polygon
    with rio.open(raster_path) as rast:
        raster_bb = rast.bounds
    print("Raster bounding box {}".format(raster_bb))
    raster_bb_poly = box(*raster_bb)  # convert bounding box to Shapely polygon

    # Clip the geodataframe with the bounding box poly
    # clip_pt_gdf = gpd.clip(pt_gdf, raster_bb_poly)  # Clip is new in geopandas 0.7 which requires Python 3.8
    clip_pt_gdf = pt_gdf[pt_gdf.geometry.intersects(raster_bb_poly)]
    print("Point data bounds after clip {}".format(clip_pt_gdf.geometry.total_bounds))

    print("Clipping time for point data: {}".format(time_elapsed(start_time)))

    return clip_pt_gdf


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

    # Convert SRTM unique to a Raster
    with rio.open(out_raster_path, 'w', **raster_unique_meta) as dst:
        dst.write(raster_uniqueid_np, 1)

    print("Create Unique ID execution time for {0}: {1}".format(out_raster_path, time_elapsed(start_time)))


def main(raster_source, uniqueid_file, work_dir, input_pt_feather, out_feather):

    pt_data_source = os.path.join(work_dir, input_pt_feather)
    out_feather_path = os.path.join(work_dir, out_feather)

    #--- Load the points
    print("Loading data from: {}".format(pt_data_source))
    start_time = time.time()
    in_pts = from_geofeather(os.path.join(work_dir, pt_data_source))
    print("Load time for {0}: {1}".format(pt_data_source, time_elapsed(start_time)))
    print(in_pts.dtypes)
    print(in_pts)

    # Clip the points to raster extent
    # in_pts_clip = clip_pts_with_raster(in_pts[1:100], raster_source)  # subset for testing
    in_pts_clip = clip_pts_with_raster(in_pts, raster_source)

    # Sample the raster
    in_pts_clip = sample_raster(in_pts_clip, raster_source, 'tncdep_m')
    print(in_pts_clip.dtypes)
    print(in_pts_clip)

    # Create unique index value for SRTM raster
    raster_unique_source = os.path.join(work_dir, uniqueid_file)
    make_unique_raster(raster_source, raster_unique_source)
    # Sample Unique ID SRTM raster
    in_pts_clip = sample_raster(in_pts_clip, raster_unique_source, 'tncdep_idx')
    in_pts_clip.reset_index(inplace=True)
    print(in_pts_clip.dtypes)
    print(in_pts_clip)

    # Export to Feather format
    print("Exporting to Geofeather format")
    start_time = time.time()
    to_geofeather(in_pts_clip, out_feather_path)
    print("Export execution time for {0}: {1}".format(out_feather_path, time_elapsed(start_time)))


#### ---- SETUP and call main function ----------

if __name__ == '__main__':

    # ------ GLiHT AMIGACarb_Out_of_the_Yuc_GLAS_May2013 data --------------
    tnc_bathy_dir = '/Users/arbailey/natcap/idb/data/source/tnc/bathy_mar/S2_Bathy_MAR_North_msk'
    tnc_bathy_file = 'S2_Bathy_MAR_North_msk.dat'
    tnc_bathy_file_path = os.path.join(tnc_bathy_dir, tnc_bathy_file)
    tnc_bathy_unique_id_file = 'S2_Bathy_MAR_North_msk_uniqueid.tif'
    working_dir = '/Users/arbailey/natcap/idb/data/work/bathy'
    conabio_bathy_feather = 'conabio_batimv2uw_pts.feather'
    out_feather = 'bathy_conabio_tncMARnorth.feather'
    main(tnc_bathy_file_path, tnc_bathy_unique_id_file, working_dir, conabio_bathy_feather, out_feather)