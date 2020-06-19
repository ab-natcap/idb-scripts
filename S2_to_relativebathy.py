""" S2_to_relativebathy.py

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


def mask_raster(raster_np, masking_np, threshold):
    """
    Mask input raster band (Blue or Green) with threshold applied to the masking array (SWIR)
    Also mask any NAN values in the input array
    :param raster_np:  input raster
    :param masking_np:   raster used for masking
    :param threshold:  threshold to use for masking
   :return: masked_np:   output masked raster in numpy masked array format
    """
    masked_np = np.ma.masked_invalid(raster_np)
    masked_np = np.ma.masked_where(masking_np > threshold, masked_np)
    return masked_np


def stumpf_ratio(band_n, band_d):
    """

    Calculate Stumpf ratio with constant (n) set to 1000, per Caballero & Stumpf, 2019
    :param band_n: band used for the numerator of the ratio (usually the blue band)
    :param band_d: band used for the denominator of the ratio (usually green or red bands)
    :return: ratio_np:  output of ratio of bands as a NumPy array
    """
    n = 1000
    ratio_np = np.log(n * band_n) / np.log(n * band_d)
    return ratio_np


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



def main(tile, masking_threshold, source_dir, out_dir):
    # Main Script to convert Reflectance to

    # Find associated band files from the source data
    os.chdir(source_dir)
    # This code assumes there is only one matching data set for the specific tile
    S2_L2R_blue = glob.glob('S2*MSI*' + tile + '_rhos_49*.tif')[0]
    S2_L2R_green = glob.glob('S2*MSI*' + tile + '_rhos_5*.tif')[0]
    S2_L2R_red = glob.glob('S2*MSI*' + tile + '_rhos_6*.tif')[0]
    S2_L2R_swir = glob.glob('S2*MSI*' + tile + '_rhos_16*.tif')[0]
    print("Input rasters:")
    print (S2_L2R_blue)
    print(S2_L2R_green)
    print(S2_L2R_red)
    print(S2_L2R_swir)

    # Convert input Blue,Green,Red, SWIR reflectance rasters to NumPy format
    blue_np, blue_profile = raster2np(S2_L2R_blue)
    green_np, green_profile = raster2np(S2_L2R_green)
    red_np, red_profile = raster2np(S2_L2R_red)
    swir_np, swir_profile = raster2np(S2_L2R_swir)

    # Mask the blue and green bands
    blue_masked = mask_raster(blue_np, swir_np, masking_threshold)
    green_masked = mask_raster(green_np, swir_np, masking_threshold)
    red_masked = mask_raster(red_np, swir_np, masking_threshold)

    # Calculate Relative Bathy with Stumpf Ratio method
    blue_red_ratio = stumpf_ratio(blue_masked, red_masked)
    blue_green_ratio = stumpf_ratio(blue_masked, green_masked)

    # Export relative bathy to GeoTiff
    print("output rasters:")
    # Blue/Red ratio
    redratio_out_file = tile + "_relbathy_red.tif"
    redratio_out_path = os.path.join(out_dir, redratio_out_file)
    export_raster(blue_red_ratio, blue_profile, redratio_out_path)
    print(redratio_out_path)
    # Blue/Green ratio
    greenratio_out_file = tile + "_relbathy_grn.tif"
    greenratio_out_path = os.path.join(out_dir, greenratio_out_file)
    export_raster(blue_green_ratio, blue_profile, greenratio_out_path)
    print(greenratio_out_path)



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
    masking_threshold = 0.08
    source_dir = '/Users/arbailey/natcap/idb/data/work/sentinel/acolite'
    work_dir = '/Users/arbailey/natcap/idb/data/work/sentinel'

    for tile in tiles:
        print(tile)
        main(tile, masking_threshold, source_dir, work_dir)