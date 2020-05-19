""" bathy_conabio_prep.py

Author: Allison Bailey
Date: 2020-05-01

Convert CONABIO bathy grids to merged point data set
Output to geofeather file for subsequent processing

Assumes input data are in 32616  (UTM 16N, WGS-84) and output data are in 4326 (lat/long WGS-84)

"""
import os
import numpy as np
import rasterio as rio
import pandas as pd
import geopandas as gpd
import fiona
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


def get_valid_indices(msked_array):
    # Return tuples of indices for valid (unmasked) values in a masked array
    rows, cols = np.where(~msked_array.mask)
    indices = list(zip(rows, cols))
    return indices


def raster_to_points(raster_source, cols, type):
    # Create point data frame from masked raster and reproject to EPSG 4326

    print("Processing {}".format(raster_source))

    # Read raster into a masked numpy array
    with rio.open(raster_source) as src:
        raster_np = src.read(1, masked=True)  # as NumPy masked array
        # Does not automatically mask nan values, so update the mask (in place)
        raster_np = np.ma.masked_invalid(raster_np, copy=False)
        raster_meta = src.meta
        print(raster_meta)
        # Cell indices for valid values (non-masked) in the raster
        indices = get_valid_indices(raster_np)
        # Initiate arrays to store x,y,z values from raster
        x_coords = []
        y_coords = []
        vals = []
        # Get x,y coords in projection and associated value
        for row, col in indices:
            x, y = src.xy(row, col)
            val = raster_np[row][col]
            x_coords.append(x)
            y_coords.append(y)
            vals.append(val)
    print(x_coords[250], y_coords[250], vals[250])  # print an example

    # Create Pandas Data Frame with x, y, z values -- set of parallel lists
    # The data as a set of parallel lists
    rasterpts_xyz = {
        cols['z']: vals,
        cols['x']: x_coords,
        cols['y']: y_coords
    }
    pts_df = pd.DataFrame(rasterpts_xyz)
    print(pts_df)

    # Return a simple data frame or geodataframe depending on type requested
    if type == 'df':
        return pts_df

    elif type == 'gdf':
        pts_gdf = gpd.GeoDataFrame(pts_df, geometry=gpd.points_from_xy(pts_df[cols['x']], pts_df[cols['y']]))
        print(pts_gdf)

        # Get CRS from input raster and convert it to right format to assign to CRS of GeoData Frame
        raster_epsg = raster_meta['crs'].to_epsg()
        pts_gdf.crs = fiona.crs.from_epsg(raster_epsg)

        # Reproject points to EPSG 4326
        pts_latlon_gdf = pts_gdf.to_crs(epsg=4326)
        print(pts_latlon_gdf)

        return pts_latlon_gdf


def main(in_dir, in_file, out_dir, out_layer):
    # Main Script to convert raster to points and export to Geofeather

    # Define output columns
    out_columns = {
        'x': 'x_utm16n',
        'y': 'y_utm16n',
        'z': 'depth_m',
    }
    # Create point geodataframe from raster
    raster_file_path = os.path.join(in_dir, in_file)
    print("Processing {}".format(raster_file_path))

    start_time = time.time()
    out_gdf = raster_to_points(raster_file_path, out_columns, type='gdf')
    print(out_gdf)
    print("Raster to points conversion time {0}: {1}".format(in_file, time_elapsed(start_time)))

    #  Export final Geodataframe to Geofeather format
    print("Exporting to Geofeather format")
    geofeather_path = os.path.join(out_dir, "{}.feather".format(out_layer))
    start_time = time.time()
    to_geofeather(out_gdf, geofeather_path)
    print("Export execution time for {0}: {1}".format(geofeather_path, time_elapsed(start_time)))




#### ---- SETUP and call main function ----------

if __name__ == '__main__':

    # Top level data directory

    conabio_bathy_dir = '/Users/arbailey/natcap/idb/data/source/conabio/batimv2gw_c'
    conabio_bathy_file = 'batimv2uw.tif'
    dest_dir = '/Users/arbailey/natcap/idb/data/work/bathy'
    out_layer = 'conabio_batimv2uw_pts'

    main(conabio_bathy_dir, conabio_bathy_file, dest_dir, out_layer)
