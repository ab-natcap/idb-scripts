""" sargassum_area_recur_compile.py

Author: Allison Bailey
Date: 2022-08-03

Compile sargassum metrics output from s2_sargassum_metrics.py
Into single polygon layer(s) for area and recurrence
Transfer these data to shoreline segment layer using attribute join

"""

import os
import geopandas as gpd
import pandas as pd

def append_lyrs(layers, cols, new_col, gpkg):
    """
    Append all layers in the dictionary into a single geodataframe
    Assumes they all have the same spatial reference

    :param layers: input layer dictionary with new attribute value as key
    :param cols: output columns for the new geodataframe
    :param gpkg: full path to geopackage with input layers
    :return:  geodataframe with all layers appended
    """
    cols.append(new_col)
    # output_gdf = gpd.GeoDataFrame(columns=cols, geometry='geometry')
    input_gdfs = []
    for idx, (layerid, lyr) in enumerate(layers.items()):
        src_gdf = gpd.read_file(gpkg, layer=lyr)
        print(layerid,lyr)
        print(idx)
        src_gdf[new_col] = layerid  # Add the layerid (time period) to source geodataframe
        input_gdfs.append(src_gdf) # Add source geodataframe with new column to list of input geodfs
    # Concatenate all the input geodataframes (with new time period column)
    out_gdf = gpd.GeoDataFrame(pd.concat(input_gdfs, ignore_index=True),columns=cols, geometry='geometry')
    return out_gdf

def poly_to_segments(poly_gdf, seg_gdf):
    """
    Join the attributes of the polygons to the segment geometry

    :param poly_gdf: Polygons with attributes by segment id
    :param seg_gdf: Segments with unique segment id to join with polygon attributes
    :return: a joined layer -- segment geometry and attributes for associated polygon region
    """
    poly_atts_df = pd.DataFrame(poly_gdf.drop(columns='geometry')) # get just attributes of poly GDF
    segments_poly_atts_gdf = seg_gdf.merge(poly_atts_df, on='seg5k_id') # Join poly attributes to segments
    return segments_poly_atts_gdf

if __name__ == '__main__':

    # Source/working directories, geopackage, layers and shapefiles
    work_dir = '/Users/arbailey/Google Drive/My Drive/sargassum/paper2022/data/work/'
    gpkg = 'os2022.gpkg'
    work_gpkg = os.path.join(work_dir, gpkg)
    print(work_gpkg)
    segments_layer = "shoreQR_5km_segments"

    # attribute to hold the time period the data represent
    layerid_col = 'timeperiod'
    # Columns to keep from the recurrence and area layers
    recur_columns = ['seg5k_id','pstmax','pstmean','pstcount','pstmedian','geometry']
    area_cols = ['seg5k_id','pxlcount','s2area_m2','geometry']

    # Load the segments layer from geopackage
    segments_gdf = gpd.read_file(work_gpkg, layer=segments_layer)

    def compile_annual():
        #  ---- RUN ANNUAL LAYERS COMPILATION
        # Inputs
        ##  Annual - single year or a range of years together
        persist_layers_annual = {
            '2016':'s2qr_persistence_20160427_20161223',
            '2017':'s2qr_persistence_20170112_20171228',
            '2018':'s2qr_persistence_20180112_20181208',
            '2019':'s2qr_persistence_20190112_20191228',
            '2020':'s2qr_persistence_20200102_20201122',
            '2021':'s2qr_persistence_20210121_20211222',
            '2017-2021':'s2qr_persistence_20170112_20211222'
        }
        area_layers_annual = {
            '2016': 's2qr_area_20160427_20161223',
            '2017': 's2qr_area_20170112_20171228',
            '2018': 's2qr_area_20180112_20181208',
            '2019': 's2qr_area_20190112_20191228',
            '2020': 's2qr_area_20200102_20201122',
            '2021': 's2qr_area_20210121_20211222',
            '2017-2021': 's2qr_area_20170112_20211222'
        }
        # Output Polygon Layers
        recur_layer_annual = 's2qr_sarg_recur_annual'
        area_layer_annual = 's2qr_sarg_area_annual'

        # Output Segment Layers
        segment_recur_layer_annual = 'seg5k_sarg_recur_annual'
        segment_area_layer_annual = 'seg5k_sarg_area_annual'

        # Annual Persistence
        merged_recur_gdf = append_lyrs(persist_layers_annual, recur_columns, layerid_col, work_gpkg)
        print(merged_recur_gdf.columns)
        print(merged_recur_gdf)
        # merged_recur_gdf.to_file(work_gpkg, layer=recur_layer_annual, driver="GPKG")

        # Annual Area
        merged_area_gdf = append_lyrs(area_layers_annual, area_cols, layerid_col, work_gpkg)
        print(merged_area_gdf.columns)
        print(merged_area_gdf)
        # merged_area_gdf.to_file(work_gpkg, layer=area_layer_annual, driver="GPKG")

        # Transfer Persistence & ARea Attributes to Segments
        segs_recur_gdf = poly_to_segments(merged_recur_gdf, segments_gdf)
        segs_area_gdf = poly_to_segments(merged_area_gdf, segments_gdf)
        # Export Persistence & Area Segments
        segs_recur_gdf.to_file(work_gpkg, layer=segment_recur_layer_annual, driver="GPKG")
        segs_area_gdf.to_file(work_gpkg, layer=segment_area_layer_annual, driver="GPKG")

        #  ---- END ANNUAL LAYERS COMPILATION

    def compile_seasonal():
        #  ---- RUN SEASONAL LAYERS COMPILATION
        print('running seasonal compilation')
        # Inputs
        ##  Seasonal - single year or a range of years together
        persist_layers = {
            '2017-2021 m010203':'s2qr_persistence_20170112_20211222_m010203',
            '2017-2021 m040506':'s2qr_persistence_20170112_20211222_m040506',
            '2017-2021 m070809':'s2qr_persistence_20170112_20211222_m070809',
            '2017-2021 m101112':'s2qr_persistence_20170112_20211222_m101112'
        }
        area_layers = {
            '2017-2021 m010203': 's2qr_area_20170112_20211222_m010203',
            '2017-2021 m040506': 's2qr_area_20170112_20211222_m040506',
            '2017-2021 m070809': 's2qr_area_20170112_20211222_m070809',
            '2017-2021 m101112': 's2qr_area_20170112_20211222_m101112'
        }
        # Output Polygon Layers
        recur_layer_out = 's2qr_sarg_recur_seasonal'
        area_layer_out = 's2qr_sarg_area_seasonal'

        # Output Segment Layers
        segment_recur_layer = 'seg5k_sarg_recur_seasonal'
        segment_area_layer = 'seg5k_sarg_area_seasonal'

        # Seasonal Persistence
        merged_recur_gdf = append_lyrs(persist_layers, recur_columns, layerid_col, work_gpkg)
        print(merged_recur_gdf.columns)
        print(merged_recur_gdf)
        merged_recur_gdf.to_file(work_gpkg, layer=recur_layer_out, driver="GPKG")

        # Seasonal Area
        merged_area_gdf = append_lyrs(area_layers, area_cols, layerid_col, work_gpkg)
        print(merged_area_gdf.columns)
        print(merged_area_gdf)
        merged_area_gdf.to_file(work_gpkg, layer=area_layer_out, driver="GPKG")

        # Transfer Persistence & ARea Attributes to Segments
        segs_recur_gdf = poly_to_segments(merged_recur_gdf, segments_gdf)
        segs_area_gdf = poly_to_segments(merged_area_gdf, segments_gdf)
        # Export Persistence & Area Segments
        segs_recur_gdf.to_file(work_gpkg, layer=segment_recur_layer, driver="GPKG")
        segs_area_gdf.to_file(work_gpkg, layer=segment_area_layer, driver="GPKG")

        #  ---- END SEASONAL LAYERS COMPILATION

    # Which set to run
    # compile_annual()
    compile_seasonal()