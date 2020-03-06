""" gliht_prep.py

Author: Allison Bailey
Date: 2020-02-28

Convert G-LiHT grids to merged point data set
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

def get_valid_indices(msked_array):
    # Return tuples of indices for valid (unmasked) values in a masked array
    rows, cols = np.where(~msked_array.mask)
    indices = list(zip(rows, cols))
    return indices

def getfilelist(in_file):
    # Get a list of files from an input text file
    files = [line.rstrip('\n') for line in open(in_file)]
    print(files)
    return files

def process_files(in_chmdir, in_chmfiles, in_dtmdir, in_dtmfiles, out_dir, out_layer):

    ## -------- DTM ------------
    # Create point geodataframes from DTM tif files in file list
    dtm_columns = {
        'x': 'x_utm16n',
        'y': 'y_utm16n',
        'z': 'z_dtm_m',
    }
    out_dtm_gdfs = []
    for file in in_dtmfiles:
        print("Processing {}".format(file))
        dtm_file_path = os.path.join(in_dtmdir, file)
        dtm_gdf = raster_to_points(dtm_file_path, dtm_columns, type='gdf')
        out_dtm_gdfs.append(dtm_gdf)
    print("{} DTM data frames combined".format(len(out_dtm_gdfs)))

    # Concat all the point DTM gdfs into a single gdf
    print("Concatenating DTM geodataframes")
    concat_dtm_gdf = pd.concat(out_dtm_gdfs, axis=0, ignore_index=True)
    # Add a unique ID for each point
    concat_dtm_gdf['gliht_ptidx'] = concat_dtm_gdf.index + 1
    concat_dtm_gdf['gliht_ptid'] = concat_dtm_gdf[dtm_columns['x']].astype(str) + "_" + concat_dtm_gdf[dtm_columns['y']].astype(str)
    print(concat_dtm_gdf)

    ## --------- CHM ------------
    # Create point geodataframes from CHM tif files in file list
    chm_columns = {
        'x': 'x_utm16n',
        'y': 'y_utm16n',
        'z': 'z_chm_m',
    }
    out_chm_dfs = []
    for file in in_chmfiles:
        print("Processing {}".format(file))
        chm_file_path = os.path.join(in_chmdir, file)
        chm_df = raster_to_points(chm_file_path, chm_columns, type='df')
        out_chm_dfs.append(chm_df)
    print("{} CHM data frames combined".format(len(out_chm_dfs)))

    # Concat all the point CHM gdfs into a single gdf
    print("Concatenating CHM geodataframes")
    concat_chm_df = pd.concat(out_chm_dfs, axis=0, ignore_index=True)
    print(concat_chm_df)

    #----------- Join and Export -------------
    # Join the CHM and the DTM GeoDataframes
    print("Joining CHM and DTM Geodataframes")
    chm_dtm_gdf = pd.merge(concat_dtm_gdf, concat_chm_df, how='left',on=[dtm_columns['x'], dtm_columns['y']])
    print(chm_dtm_gdf)

    #  Export final Geodataframe
    print("Exporting to Geofeather format")
    geofeather_path = os.path.join(dest_dir, "{}.feather".format(out_layer))
    to_geofeather(chm_dtm_gdf, geofeather_path)

    # # export to Geopackage
    # print("Exporting to Geopackage")
    # chm_dtm_gdf.to_file(os.path.join(out_dir, "gliht_yucatan.gpkg"), layer=out_layer, driver="GPKG")


def raster_to_points(raster_source, cols, type):

    print("Processing {}".format(raster_source))

    # Read GLiHT data into a masked numpy array
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
    # print(x_coords[250], y_coords[250], vals[250])  # print an example

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

        # Get CRS from GLiHT and convert it to right format to assign to CRS of GeoData Frame
        raster_epsg = raster_meta['crs'].to_epsg()
        pts_gdf.crs = fiona.crs.from_epsg(raster_epsg)

        # Reproject GLiHT points to SRTM CRS
        pts_latlon_gdf = pts_gdf.to_crs(epsg=4326)
        print(pts_latlon_gdf)

        return pts_latlon_gdf



#### ---- SETUP and call main function ----------

if __name__ == '__main__':

    # Top level data directory
    source_dir = '/Users/arbailey/natcap/idb/data/source/gliht/'
    dest_dir = '/Users/arbailey/natcap/idb/data/work/mangroves/yucatan'
    out_geopackage = 'gliht_yucatan.gpkg'

    # in_dir = os.path.join(source_dir, 'AMIGACarb_Out_of_the_Yuc_GLAS_May2013/lidar/geotiff/AMIGACarb_Out_of_the_Yuc_GLAS_May2013_CHM')
    # in_file = 'AMIGACarb_Out_of_the_Yuc_GLAS_May2013_l1s447_CHM.tif'
    # out_lyr = 'gliht_yucatan_east_subset'

    # # Process CHM and DTM from AMIGACarb_Out_of_the_Yuc_GLAS_May2013  (eastern side of Yucutan)
    # test_chm_dir = os.path.join(source_dir, 'AMIGACarb_Out_of_the_Yuc_GLAS_May2013/lidar/geotiff/AMIGACarb_Out_of_the_Yuc_GLAS_May2013_CHM')
    # test_dtm_dir = os.path.join(source_dir, 'AMIGACarb_Out_of_the_Yuc_GLAS_May2013/lidar/geotiff/AMIGACarb_Out_of_the_Yuc_GLAS_May2013_DTM')
    # test_chm_listfile = 'test_CHM.txt'
    # test_dtm_listfile = 'test_DTM.txt'
    # test_chm_files = getfilelist(os.path.join(test_chm_dir, test_chm_listfile))
    # test_dtm_files = getfilelist(os.path.join(test_dtm_dir, test_dtm_listfile))
    # test_out_lyr = 'test_gliht_yucatan_east_subset'
    #
    # process_files(test_chm_dir, test_chm_files, test_dtm_dir, test_dtm_files, dest_dir, test_out_lyr)

    # # Process CHM and DTM from AMIGACarb_Out_of_the_Yuc_GLAS_May2013  (eastern side of Yucutan)
    # yuceast_chm_dir = os.path.join(source_dir, 'AMIGACarb_Out_of_the_Yuc_GLAS_May2013/lidar/geotiff/AMIGACarb_Out_of_the_Yuc_GLAS_May2013_CHM')
    # yuceast_dtm_dir = os.path.join(source_dir, 'AMIGACarb_Out_of_the_Yuc_GLAS_May2013/lidar/geotiff/AMIGACarb_Out_of_the_Yuc_GLAS_May2013_DTM')
    # yuceast_chm_listfile = 'Out_of_the_Yuc_CHM_mangroveoverlap.txt'
    # yuceast_dtm_listfile = 'Out_of_the_Yuc_DTM_mangroveoverlap.txt'
    # yuceast_chm_files = getfilelist(os.path.join(yuceast_chm_dir, yuceast_chm_listfile))
    # yuceast_dtm_files = getfilelist(os.path.join(yuceast_dtm_dir, yuceast_dtm_listfile))
    # yuceast_out_lyr = 'gliht_yucatan_east_subset'
    #
    # process_files(yuceast_chm_dir, yuceast_chm_files, yuceast_dtm_dir, yuceast_dtm_files, dest_dir, yuceast_out_lyr)

    # Process CHM and DTM from AMIGACarb_Yuc_Norte_GLAS_Apr2013  (western side of Yucutan)
    yucwest_chm_dir = os.path.join(source_dir, 'AMIGACarb_Yuc_Norte_GLAS_Apr2013/lidar/geotiff/AMIGACarb_Yuc_Norte_GLAS_Apr2013_CHM')
    yucwest_chm_listfile = 'Yuc_Norte_CHM_mangroveoverlap.txt'
    yucwest_chm_files = getfilelist(os.path.join(yucwest_chm_dir, yucwest_chm_listfile))
    yucwest_dtm_dir = os.path.join(source_dir, 'AMIGACarb_Yuc_Norte_GLAS_Apr2013/lidar/geotiff/AMIGACarb_Yuc_Norte_GLAS_Apr2013_DTM')
    yucwest_dtm_listfile = 'Yuc_Norte_DTM_mangroveoverlap.txt'
    yucwest_dtm_files = getfilelist(os.path.join(yucwest_dtm_dir, yucwest_dtm_listfile))
    yucwest_out_lyr = 'gliht_yucatan_west_subset'

    process_files(yucwest_chm_dir, yucwest_chm_files, yucwest_dtm_dir, yucwest_dtm_files, dest_dir, yucwest_out_lyr)



