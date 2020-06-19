""" S2_relative_to_depth.py

Author: Allison Bailey
Date: 2020-06-18

Take Raster file inputs for Blue, Green, SWIR reflectance and create masked relative bathy TIF
Assumes input data have been processed via ACOLITE atmospheric correction algorithm
"""

# Import Libraries
import os
import glob
import numpy as np
import rasterio
from rasterio import Affine

# m0 and m1 parameters from linear regression of relative bathymetry with depth points
# For Blue/Green ratio
parameters_green = {
    'T16PCC': [0, 0],
    'T16PDC': [0, 0],
    'T16PEC': [0, 0],
    'T16QCD': [0, 0],
    'T16QDD': [0, 0],
    'T16QDE': [0, 0],
    'T16QDF': [-95.95551986, 100.06296858],  # r2 = 0.767
    'T16QED': [0, 0],
    'T16QFD': [0, 0],
    'T16QCE': [0, 0],
    'T16PBC': [0, 0],
    'T16PFC': [0, 0],
}
# For Blue/Red ratio
parameters_red = {
    'T16PCC': [0, 0],
    'T16PDC': [0, 0],
    'T16PEC': [0, 0],
    'T16QCD': [0, 0],
    'T16QDD': [0, 0],
    'T16QDE': [0, 0],
    'T16QDF': [-11.82141448, 11.88684666],  # r2 = 0.267
    'T16QED': [0, 0],
    'T16QFD': [0, 0],
    'T16QCE': [0, 0],
    'T16PBC': [0, 0],
    'T16PFC': [0, 0],
}

def raster2np(source_raster):
    """
    Convert a raster file to numpy format with rasterio.  include the metadata profile
    :param source_path: input raster file
    :return: raster_np: raster data as a numpy array
            profile: metadata profile for the raster
    """

    with rasterio.open(source_raster) as src:
        profile = src.profile
        raster_np = src.read(1)
    return [raster_np, profile]


def calc_depth(relativebathy_np, m0, m1):
    """

    Calculate absolute depth value from relative bathymetry with m0 and m1 tunable parameters per Stumpf 2003
    :param rb_np: relative bathymetry as a NumPy array
    :param m0: m0 constant (Stumpf 2003) from relative bathy/depth point regression
    :param m1: m1 constant (Stumpf 2003) from relative bathy/depth point regression
    :return: bathy_np:  output of ratio of bands as a NumPy array
    """

    depth_np = m1 * (relativebathy_np) + m0
    return depth_np


def export_raster(raster_np, profile, out_filepath):
    """

    :param raster_np: Input raster as NumPy format
    :param profile: metadata profile of input raster
    :param out_filepath: output file path
    :return:
    """
    # Fill masked cells with no data value
    nodatavalue = -9999.0
    raster_nd = np.ma.filled(raster_np, fill_value=nodatavalue)
    # Create Profile for raster to export and update with no data value
    new_profile = profile
    new_profile.update({'nodata': nodatavalue})

    # Export to Raster file
    with rasterio.open(out_filepath, 'w', **new_profile) as outf:
        outf.write(raster_nd, 1)


def main(tile, work_dir):
    # Main Script to convert Reflectance to

    # Find associated band files from the source data
    os.chdir(work_dir)
    # This code assumes there is only one matching data set for the specific tile
    relbathy_green = tile + "_relbathy_grn.tif"
    relbathy_red = tile + "_relbathy_red.tif"
    print("Input rasters:")
    print (relbathy_green)
    print(relbathy_red)

    # Convert relative bathy rasters to NumPy format
    rb_green_np, rb_green_profile = raster2np(relbathy_green)
    rb_red_np, rb_red_profile = raster2np(relbathy_red)
    print(rb_green_profile)
    print(rb_red_profile)
    # print(rb_green_np)
    # print(rb_red_np)
    # Mask No Data values
    rb_red_masked = np.ma.masked_values(rb_red_np, rb_red_profile['nodata'])
    rb_green_masked = np.ma.masked_values(rb_green_np, rb_green_profile['nodata'])

    # Calculate Depth from regression parameters
    # Blue / Green ratio
    m0_green = parameters_green[tile][0]
    m1_green = parameters_green[tile][1]
    # print(m0_green)
    # print(m1_green)
    bathy_green = calc_depth(rb_green_masked, m0_green, m1_green)
    # Blue / Red ratio
    m0_red = parameters_red[tile][0]
    m1_red = parameters_red[tile][1]
    bathy_red = calc_depth(rb_red_masked, m0_red, m1_red)

    print(bathy_green)
    print(bathy_red)

    # Export bathy to GeoTiff
    out_dir = work_dir
    print("output rasters:")
    # Blue/Green ratio SDB output
    greensdb_out_file = tile + "_sdb_grn.tif"
    greensdb_out_path = os.path.join(out_dir, greensdb_out_file)
    export_raster(bathy_green, rb_green_profile, greensdb_out_path)
    print(greensdb_out_path)
    # Blue/Red ratio SDB output
    redsdb_out_file = tile + "_sdb_red.tif"
    redsdb_out_path = os.path.join(out_dir, redsdb_out_file)
    export_raster(bathy_red, rb_red_profile, redsdb_out_path)
    print(redsdb_out_path)




#### ---- SETUP and call main function ----------

if __name__ == '__main__':

    tiles = [
        'T16PCC',
        'T16PDC',
        'T16PEC',
        'T16QCD',
        'T16QDD',
        'T16QDE',
        'T16QDF',
        'T16QED',
        'T16QFD',
        'T16QCE',
        'T16PBC',
        'T16PFC',
    ]

    # Subset of tiles for testing
    tiles = [
        'T16QDF',
    ]



    work_dir = '/Users/arbailey/natcap/idb/data/work/sentinel'

    for tile in tiles:
        print(tile)
        main(tile, work_dir)