""" mask_raster.py

Author: Allison Bailey
Date: 2020-02-06

Mask the grids with  vector polygons

Assumes all geographic data are in the same projection

"""

import os
import glob
import fiona
import rasterio
import rasterio.mask

def add_prefix(filename, prefix):
    return '{}_{}'.format(prefix, filename)

def mask_raster(in_raster_file, mask_file, out_raster_file):
    """

    Main script to mask grids with polygons
    Thanks to:  https://rasterio.readthedocs.io/en/latest/topics/masking-by-shapefile.html
        https://rasterio.readthedocs.io/en/latest/api/rasterio.mask.html
    :param in_raster_file: input raster file
    :param mask_file: polygon layer used to mask the raster
    :param out_raster_file: output raster file
    :return:

    """
    print(in_raster_file, mask_file, out_raster_file)

    with fiona.open(mask_file, "r") as mask_file:
        shapes = [feature["geometry"] for feature in mask_file]

    with rasterio.open(in_raster_file)as src:
        out_image, out_transform = rasterio.mask.mask(src, shapes, all_touched=True, crop=True)
        out_meta = src.meta

    out_meta.update({"driver": "GTiff",
                     "height": out_image.shape[1],
                     "width": out_image.shape[2],
                     "transform": out_transform})

    with rasterio.open(out_raster_file, "w", **out_meta) as dest:
        dest.write(out_image)


#### ---- SETUP and call main function ----------

if __name__ == '__main__':

    # Top level data directory
    data_dir = '/Users/arbailey/natcap/idb/data/work/mangroves'

    # Vector shapefile paths
    # World Atlas of Mangroves
    wam_path = os.path.join(data_dir, 'wam_Bahamas_MAR.shp')
    wam_prefix = 'wam'
    # Global Mangrove Watch
    gmw2016_path = os.path.join(data_dir, 'gmw2016_Bahamas_MAR.shp')
    gmw2016_prefix = 'gmw2016'
    # Global Mangrove Forests (Andros)
    gmf_path = os.path.join(data_dir, 'gmf_andros.shp')
    gmf_prefix = 'gmf'
    # TNC Landsat Mangroves
    tnc_path = os.path.join(data_dir, 'tnc_mangroves_andros.shp')
    tnc_prefix = 'tnc'

    # Input Raster
    # hgt_raster = 'Andros_TDX_DEM_12m_EGM2008_CanopyHeight.tif'  # original - 2020-02-05
    # in_raster_dir = '/Users/arbailey/natcap/idb/data/source/nasa/Andros_12m_CHM_AGB'  # original
    hgt_raster = 'Andros_TDX_DEM_12m_EGM2008_CHM_Cal_mask.tif'  # updated - 2020-02-18
    in_raster_dir = '/Users/arbailey/natcap/idb/data/source/nasa/TDXCHMAGBAndros'  # updated
    in_raster = os.path.join(in_raster_dir, hgt_raster)

    # Working directory
    work_dir = os.path.join(data_dir, 'tandemx')
    os.chdir(work_dir)

    # WAM mask
    wam_hgt_raster = add_prefix(hgt_raster, wam_prefix)
    mask_raster(in_raster, wam_path, wam_hgt_raster)

    # GMW 2016 mask
    gmw2016_hgt_raster = add_prefix(hgt_raster, gmw2016_prefix)
    mask_raster(in_raster, gmw2016_path, gmw2016_hgt_raster)

    # GMF mask
    gmf_hgt_raster = add_prefix(hgt_raster, gmf_prefix)
    mask_raster(in_raster, gmf_path, gmf_hgt_raster)

    # TNC Landsat mask
    tnc_hgt_raster = add_prefix(hgt_raster, tnc_prefix)
    mask_raster(in_raster, tnc_path, tnc_hgt_raster)

