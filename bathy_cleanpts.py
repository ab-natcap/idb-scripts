""" bathy_cleanpts.py

Author: Allison Bailey
Date: 2020-06-24

Take raster X,Y,Z file and remove no data values, standardize depth value & sign & output to shapefile
"""

# Import Libraries
import pandas as pd
import geopandas as gpd

# CONABIO
# source_csv = '/Users/arbailey/natcap/idb/data/work/bathy/batimv2uw_subset.csv'
# output_shapefile = '/Users/arbailey/natcap/idb/data/work/bathy/batimv2uw_subset.shp'
# TNC
# source_csv = '/Users/arbailey/natcap/idb/data/work/bathy/tncmar/tnc_BancoChincorro_masked_pts.csv'
# output_shapefile = '/Users/arbailey/natcap/idb/data/work/bathy/tncmar/tnc_BancoChincorro_masked_pts.shp'
# source_csv = '/Users/arbailey/natcap/idb/data/work/bathy/tncmar/tnc_BzIslands_masked_pts.csv'
# output_shapefile = '/Users/arbailey/natcap/idb/data/work/bathy/tncmar/tnc_BzIslands_masked_pts.shp'
source_csv = '/Users/arbailey/natcap/idb/data/work/bathy/tncmar/tnc_BzGtNearshore_masked_pts.csv'
output_shapefile = '/Users/arbailey/natcap/idb/data/work/bathy/tncmar/tnc_BzGtNearshore_masked_pts.shp'
# source_csv = '/Users/arbailey/natcap/idb/data/work/bathy/tncmar/tnc_HondurasIslands_masked_pts.csv'
# output_shapefile = '/Users/arbailey/natcap/idb/data/work/bathy/tncmar/tnc_HondurasIslands_masked_pts.shp'
# source_csv = '/Users/arbailey/natcap/idb/data/work/bathy/tncmar/tnc_Corozal_masked_pts.csv'
# output_shapefile = '/Users/arbailey/natcap/idb/data/work/bathy/tncmar/tnc_Corozal_masked_pts.shp'
# # BZ CZMAI
# source_csv = '/Users/arbailey/natcap/idb/data/source/bathy/bzczmai/bzczmai_bathy_pts.csv'
# output_shapefile = '/Users/arbailey/natcap/idb/data/work/bathy/bzczmai_bathy_pts.shp'

# No Data value and Projection info
nodataval = 0
crs = {'init': 'epsg:32616'}

sources = [
    # '/Users/arbailey/natcap/idb/data/work/bathy/batimv2uw_subset.csv',
    '/Users/arbailey/natcap/idb/data/work/bathy/tncmar/tnc_BancoChincorro_masked_pts.csv',
    # '/Users/arbailey/natcap/idb/data/work/bathy/tncmar/tnc_BzIslands_masked_pts.csv',
    # '/Users/arbailey/natcap/idb/data/work/bathy/tncmar/tnc_BzGtNearshore_masked_pts.csv',
    # '/Users/arbailey/natcap/idb/data/work/bathy/tncmar/tnc_HondurasIslands_masked_pts.csv',
    # '/Users/arbailey/natcap/idb/data/work/bathy/tncmar/tnc_Corozal_masked_pts.csv',
    # '/Users/arbailey/natcap/idb/data/source/bathy/bzczmai/bzczmai_bathy_pts.csv',
]

output_files = [
    # '/Users/arbailey/natcap/idb/data/work/bathy/batimv2uw_subset.shp'
    '/Users/arbailey/natcap/idb/data/work/bathy/tncmar/tnc_BancoChincorro_masked_pts.shp',
    # '/Users/arbailey/natcap/idb/data/work/bathy/tncmar/tnc_BzIslands_masked_pts.shp',
    # '/Users/arbailey/natcap/idb/data/work/bathy/tncmar/tnc_BzGtNearshore_masked_pts.shp',
    # '/Users/arbailey/natcap/idb/data/work/bathy/tncmar/tnc_HondurasIslands_masked_pts.shp',
    # '/Users/arbailey/natcap/idb/data/work/bathy/tncmar/tnc_Corozal_masked_pts.shp',
    # '/Users/arbailey/natcap/idb/data/work/bathy/bzczmai_bathy_pts.shp',
]

for source, outshp in zip(sources, output_files):
    print(source)
    # Import into pandas and remove entries with the No data value
    df = pd.read_csv(source_csv)  # Create a Dataframe from CSV
    df = df[df.Z != nodataval]
    print(df.head())
    # Convert to Geodataframe
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.X, df.Y), crs=crs)
    # Add column for consistent column name and sign  (works because all values are deeper than 0 depth)
    gdf['dep_m'] = gdf['Z'].abs()
    print(outshp)
    gdf.to_file(output_shapefile)
