""" reclass_sum_and_nodata_count.py

Author: Doug Denu
Date: 2022-01-05

From https://gist.github.com/dcdenu4/f0c7c93da397e03768d548162fb2c8f2

"""
import os
import sys
import logging
import glob

import numpy
from osgeo import gdal
from osgeo import osr
import pygeoprocessing

logging.basicConfig(
    level=logging.DEBUG,
    format=(
        '%(asctime)s (%(relativeCreated)d) %(levelname)s %(name)s'
        ' [%(funcName)s:%(lineno)d] %(message)s'),
    stream=sys.stdout)
LOGGER = logging.getLogger(__name__)

TARGET_NODATA = -1
TARGET_DATATYPE = gdal.GDT_Int16

def align_rasters_step(raster_path_list, intermediate_dir):
    """Make sure that all the rasters are aligned for per pixel operations.
    Args:
        raster_path_list (list): list of strings of raster file paths to align
        intermediate_dir (string): location on disk to save the aligned rasters
    Returns:
        a list of strings for the aligned raster paths
    """
    base_raster_info = pygeoprocessing.get_raster_info(raster_path_list[0])
    aligned_raster_path_list = []

    # create a list of corresponding target paths for the aligned rasters
    for raster_path in raster_path_list:
        aligned_name = os.path.splitext(os.path.basename(raster_path))[0]
        aligned_path = os.path.join(
            intermediate_dir, f'{aligned_name}_aligned.tif')
        aligned_raster_path_list.append(aligned_path)

    # setup a list of resampling methods to use for each aligned raster
    resample_method_list = ['near']*len(raster_path_list)
    target_pixel_size = base_raster_info['pixel_size']
    bounding_box_mode = 'intersection'

    pygeoprocessing.align_and_resize_raster_stack(
        raster_path_list, aligned_raster_path_list, resample_method_list,
        target_pixel_size, bounding_box_mode)

    return aligned_raster_path_list

def reclassify_rasters_step(raster_path_list, intermediate_dir):
    """Reclassify rasters.
    Args:
        raster_path_list (list): list of strings of raster file paths to
            reclassify
        intermediate_dir (string): location on disk to save reclassed rasters
    Returns:
        a list of strings for the reclassed raster paths
    """

    # reclassification value map
    reclass_map = {
        -9999: 0,
        -1: -1,
        0: 0,
        1: 1
    }

    reclassified_raster_list = []

    for raster_path in raster_path_list:
        target_name = os.path.splitext(os.path.basename(raster_path))[0]
        target_path = os.path.join(intermediate_dir, f'{target_name}_reclass.tif')
        reclassified_raster_list.append(target_path)

        pygeoprocessing.reclassify_raster(
            (raster_path, 1), reclass_map, target_path, TARGET_DATATYPE,
            TARGET_NODATA)

    return reclassified_raster_list

def sum_by_pixel(raster_path_list, out_dir):
    """Pixel sum the rasters treating nodata values as zero.
    Args:
        raster_path_list (list): list of strings of raster file paths to sum
        out_dir (string): directory location on disk to save sum raster
    Returns:
        Nothing
    """
    sum_raster_path = os.path.join(out_dir, 'sum_by_pixel.tif')

    def sum_op(*arrays):
        """Computes the per pixel sum of the arrays.
        This operation treats nodata values as 0.
        Args:
            *arrays (list): a list of numpy arrays
        Returns:
            Per pixel sums.
        """
        sum_result = numpy.full(arrays[0].shape, 0, dtype=numpy.int16)
        for array in arrays:
            valid_mask = ~numpy.isclose(array, TARGET_NODATA)
            sum_result[valid_mask] = sum_result[valid_mask] + array[valid_mask]

        return numpy.where(sum_result == 0, TARGET_NODATA, sum_result)

    # raster calculate expects a list of (raster_path, band) tuples
    raster_path_band_list = [(raster_path, 1) for raster_path in raster_path_list]
    pygeoprocessing.raster_calculator(
        raster_path_band_list, sum_op, sum_raster_path, gdal.GDT_Int16,
        TARGET_NODATA)

def nodata_count_by_pixel(raster_path_list, out_dir):
    """A nodata pixel count of rasters.
    Args:
        raster_path_list (list): list of strings of raster file paths
        out_dir (string): directory location on disk to save raster
    Returns:
        Nothing
    """
    nodata_count_raster_path = os.path.join(
        out_dir, 'nodata_count_by_pixel.tif')

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
    pygeoprocessing.raster_calculator(
        raster_path_band_list, nodata_count_op, nodata_count_raster_path,
        gdal.GDT_Int16, TARGET_NODATA)

def create_test_rasters(intermediate_dir):
    """Create 3 rasters for testing purposes.
    Args:
        intermediate_dir (string): directory location on disk to save raster
    Returns:
        List of raster paths
    """

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(32731)  # WGS84/UTM zone 31s
    wkt = srs.ExportToWkt()
    raster_path_list = []
    for temp_number in [1,2,3]:
        raster_path = os.path.join(
            intermediate_dir, f'raster_temp_{temp_number}.tif')
        int_array = numpy.ones((4,4), dtype=numpy.int16)
        int_array[1,1] = TARGET_NODATA
        int_array[temp_number, temp_number] = TARGET_NODATA
        pygeoprocessing.numpy_array_to_raster(
            int_array, TARGET_NODATA, (2, -2), (2, -2), wkt, raster_path)
        raster_path_list.append(raster_path)

    return raster_path_list

if __name__ == "__main__":
    LOGGER.debug("Starting script execution.")
    ### Get list of rasters ###
    # setup directories

    source_dir = '/Users/arbailey/Google Drive/My Drive/sargassum/s2toa_classified_v1'
    remote_base_dir = '/Users/arbailey/Google Drive/My Drive/sargassum/paper2022/data/source/s2qr_sargassum' # Remote
    local_base_dir = '/Users/arbailey/natcap/idb/data/work/sargassum/s2qr_sargassum'  # Local

    # base_dir = os.path.join('Users', 'arbailey', 'natcap', 'idb', 'data', 'work', 'sargassum')
    base_dir = local_base_dir
    # source_dir = os.path.join(base_dir, 's2qr_sargassum', 's2qr_sargassum')
    intermediate_dir = os.path.join(base_dir, 'intermediate')
    out_dir = os.path.join(base_dir, 'out')

    # create intermediate and output directories if they don't exist
    for new_dir in [intermediate_dir, out_dir]:
        if not os.path.exists(new_dir):
            os.mkdir(new_dir)

    # collect the raster paths from the source directory
    raster_path_list = [r for r in glob.glob(os.path.join(source_dir, "*mosaic_nd0.vrt"))]
    LOGGER.debug(f"Number of source rasters: {len(raster_path_list)}")

    ### Option to create rasters for testing ###
    # uncomment the below code to use three 4x4 test rasters
    #raster_path_list = create_test_rasters(intermediate_dir)

    ### Align rasters ###
    aligned_raster_list = align_rasters_step(raster_path_list, intermediate_dir)

    ### Reclass rasters ###
    reclassified_raster_list = reclassify_rasters_step(
        aligned_raster_list, intermediate_dir)

    ### Create output rasters ###
    sum_by_pixel(reclassified_raster_list, out_dir)
    nodata_count_by_pixel(reclassified_raster_list, out_dir)

    LOGGER.debug("Done.")