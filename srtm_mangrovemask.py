""" srtm_mangrovemask.py

Author: Allison Bailey
Date: 2020-01-13

Mask the SRTM grids with mangrove vector polygons

Assumes all geographic data are in the same projection (EPSG 4326)

"""

import os
import glob
import fiona
import rasterio
import rasterio.mask

def add_prefix(filename, prefix):
    return '{}_{}'.format(prefix, filename)

def main(in_raster_file, mask_file, out_raster_file):
    """

    Main script to mask SRTM grids with mangrove polygons
    Thanks to:  https://rasterio.readthedocs.io/en/latest/topics/masking-by-shapefile.html
        https://rasterio.readthedocs.io/en/latest/api/rasterio.mask.html
    :param in_raster_file: input SRTM height raster file
    :param mask_file: mangrove polygon layer used to mask the raster
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

# Top level data directory
data_dir = '/Users/arbailey/natcap/idb/data/work/mangroves'

# Working directory
work_dir = os.path.join(data_dir, 'srtm')

# Vector shapefile paths
# World Atlas of Mangroves
wam_path = os.path.join(data_dir, 'wam_Bahamas_MAR.shp')
wam_prefix = 'wam'
# Global Mangrove Watch
gmw2016_path = os.path.join(data_dir, 'gmw2016_Bahamas_MAR.shp')
gmw2016_prefix = 'gmw2016'


# Get a list of raster files with the hmax or hba prefix in the work directory
os.chdir(work_dir)
hmax_rasters = glob.glob("hmax_*.tif")
hba_rasters = glob.glob("hba_*.tif")

# Create output filenames with prefix based on mangrove data source
wam_hmax_rasters = [add_prefix(r, wam_prefix) for r in hmax_rasters]
wam_hba_rasters = [add_prefix(r, wam_prefix) for r in hba_rasters]

gmw2016_hmax_rasters = [add_prefix(r, gmw2016_prefix) for r in hmax_rasters]
gmw2016_hba_rasters = [add_prefix(r, gmw2016_prefix) for r in hba_rasters]

# WAM mask of Max Height rasters
for in_raster, out_raster in zip(hmax_rasters, wam_hmax_rasters):
    main(in_raster, wam_path, out_raster)

# WAM mask of Basal area weighted height rasters
for in_raster, out_raster in zip(hba_rasters, wam_hba_rasters):
    main(in_raster, wam_path, out_raster)

# GMW 2016 mask of Max Height rasters
for in_raster, out_raster in zip(hmax_rasters, gmw2016_hmax_rasters):
    main(in_raster, gmw2016_path, out_raster)

# GMW 2016 mask of Basal area weighted height rasters
for in_raster, out_raster in zip(hba_rasters, gmw2016_hba_rasters):
    main(in_raster, gmw2016_path, out_raster)


