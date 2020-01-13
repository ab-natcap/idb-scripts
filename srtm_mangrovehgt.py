""" srtm_mangrovehgt.py

Author: Allison Bailey
Date: 2020-01-07

Create grids of Maximum Mangrove Height and Basal Area Weighted Height from SRTM elevation grid
Using Equations from Simard et al (2019), https://doi.org/10.1038/s41561-018-0279-1

Maximum mangrove canopy height
SRTM Hmax = 1.697 x Hsrtm

Basal area weighted mangrove canopy height
SRTM Hba = 1.0754 x Hsrtm

"""

import os
import numpy as np
import rasterio as rio
import glob
#import pprint

# Simard et al (2019), https://doi.org/10.1038/s41561-018-0279-1
HMAX_MULTIPLIER = 1.697
HBA_MULTIPLIER = 1.0754


def range2datatype(data_np):
    """
    Calculate the rasterio minimum data type that will hold the range of values in the array
    :param data_np: NumPy array of data values
    :return: datatype:  minimum datatype to include the range of values in the array
    """
    min_value = np.min(data_np)
    max_value = np.max(data_np)
    datatype = rio.dtypes.get_minimum_dtype([min_value, max_value])
    return datatype


def create_raster(data_np, metadata, out_file):
    """
    Create a single band raster file from a NumPy array with the specified metadata and output filename/path
    :param data_np: Input NumPy data array
    :param metadata: Spatial metadata for output raster
    :param out_file: output raster filename or full path
    :return:
    """

    # Check datatypes of array and metadata - change array to match metadata if necessary
    if data_np.dtype != metadata['dtype']:
        data_np = data_np.astype(metadata['dtype'])

    # Create output raster
    with rio.open(out_file, 'w', **metadata) as dst:
        dst.write(data_np, 1)
    print(out_file)


def main(srtm_source):
    """
    Main script to create two mangrove height grids from SRTM grid
    :param srtm_source: path for the input SRTM raster
    :return:
    """
    # output raster variables
    out_driver = 'GTiff'  # GDAL raster driver for output raster
    out_ext = 'tif'

    with rio.open(srtm_source, driver='SRTMHGT') as srtm:
    # Get SRTM as NumPy array and it's metadata
        srtm_np = srtm.read(1)
        srtm_meta = srtm.meta
        # print(srtm.name)
        # pprint.pprint(srtm_meta)

        # Create NumPy arrays from SRTM using the corresponding multipliers for
        # Maximum Height and Basal Area Weighted Height
        hmax_np = srtm_np * HMAX_MULTIPLIER
        hba_np = srtm_np * HBA_MULTIPLIER

        # Determine the best output datatype for each height array
        hmax_datatype = range2datatype(hmax_np)
        hba_datatype = range2datatype(hba_np)

        # Create metadata for output mangrove height rasters
        # Max Height
        hmax_meta = srtm_meta  # Copy metadata from SRTM input
        hmax_meta.update({
            'dtype' : hmax_datatype,
            'driver' : out_driver
        })
        # Basal Area Weighted Height
        hba_meta = srtm_meta
        hba_meta.update({
            'dtype' : hba_datatype,
            'driver' : out_driver
        })

        # Get the source SRTM filename and pull out the first part which is the Tile identifier (looks like this: N##W###)
        filename = os.path.basename(srtm.name)
        tileid = filename.split('.')[0]

        # Filenames for Max Height and Basal Area Weighted Height output rasters
        hmax_filename = '{}_{}.{}'.format('hmax', tileid, out_ext)
        hba_filename = '{}_{}.{}'.format('hba', tileid, out_ext)

        # Create raster files
        create_raster(hmax_np, hmax_meta, hmax_filename)
        create_raster(hba_np, hba_meta, hba_filename)


### ------ Setup directories and data for input and output in the main script ----------

# Source directory, SRTM
source_dir = '/Users/arbailey/natcap/idb/data/source/srtm/nasa'
# Working and output directory
work_dir = '/Users/arbailey/natcap/idb/data/work/mangroves/srtm'

# srtm_source = os.path.join(source_dir, 'N23W078.SRTMGL1.hgt.zip')  # one file for testing

# Get a list of all files with the SRTM extension in the source directory
os.chdir(source_dir)
srtm_files = glob.glob("*.hgt.zip")
srtm_files_path = [os.path.join(source_dir, file) for file in srtm_files]  # add directory path
print(srtm_files)

# Call the main script with each source file
os.chdir(work_dir)  # Change to output directory
for srtm_source in srtm_files_path:
    main(srtm_source)









