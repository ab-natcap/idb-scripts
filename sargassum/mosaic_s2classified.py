""" mosaic_classified.py

Author: Allison Bailey
Date: 2021-03-22

Mosaic classified Sargassum Sentinel-2 Tiles by date.
Specify No Data value (-9999)
"""


import os
import subprocess
from multiprocessing import Pool
from timeit import default_timer as timer

# input_dir = r'/Users/arbailey/Google Drive/My Drive/sargassum/s2sr_classified'
# input_dir = r'/Users/arbailey/Google Drive/My Drive/sargassum/s2toa_classified'
# input_dir = r'/Users/arbailey/Google Drive/My Drive/sargassum/s2toa_classified_v3'
input_dir = r'/Users/arbailey/Google Drive/My Drive/sargassum/s2toa_classified_v1'

# gdal_nodata_command = 'gdal_edit.py -a_nodata -9999 {classed_tile}'

# https://courses.spatialthoughts.com/gdal-tools.html#running-commands-in-batch
def add_nodata(file):
    input = os.path.join(input_dir, file)
    # filename = os.path.splitext(os.path.basename(file))[0]
    # output = os.path.join(input_dir, filename + '.tif')
    # os.system(gdal_nodata_command.format(classed_tile=input)) # doesn't work with space in filename
    os.system('gdal_edit.py -a_nodata -9999 ' + '"' + input + '"')

def remove_nodata(file):
    input = os.path.join(input_dir, file)
    os.system('gdal_edit.py -unsetnodata ' + '"' + input + '"')

def mosaic2vrt(prefix):
    start_dir = os.getcwd()
    os.chdir(input_dir)
    outfile = prefix + '_mosaic.vrt'
    infiles = prefix + '*.tif'
    print(outfile)
    # One version of VRT with nodata set to -9999
    os.system('gdalbuildvrt -overwrite ' + outfile + " " + infiles)
    os.chdir(start_dir)

def mosaic2vrt_nd0(prefix):
    start_dir = os.getcwd()
    os.chdir(input_dir)
    outfile = prefix + '_mosaic_nd0.vrt'
    infiles = prefix + '*.tif'
    # Version of VRT without a No Data value (-9999 shows as value)
    os.system('gdalbuildvrt -overwrite ' + outfile + " " + infiles)
    print(outfile)
    # # Recalc the -9999 value to 0  -- Not using this part
    # # https://spatialthoughts.com/2019/12/28/gdal-calc/
    # outfile2 = prefix + '_mosaic_nd0.vrt'
    # os.system('gdal_calc.py -A ' + outfile2 + '--calc="(A<-1)*0 + (A>=-1)*1" --outfile ' + outfile1)
    os.chdir(start_dir)


if __name__ == '__main__':

    print(input_dir)

    files = [file for file in os.listdir(input_dir) if file.endswith('.tif')]

    prefixes = []
    for f in files:
        prefix = f.split('_')[0]
        if not prefix in prefixes:
            prefixes.append(prefix)
    print(prefixes)

    # ##--- Add No Data value to TIF files
    # p = Pool(4)
    # p.map(add_nodata, files)
    # ##-- Create VRT mosaics from single date classifications
    # p = Pool(4)
    # p.map(mosaic2vrt, prefixes)

    ## -- Create VRT mosaics with -9999 no data replaced with 0
    ##--- REmove no data value so -9999 are visible
    ## -- Decided to do this in Pandas before export, but may need later
    p = Pool(4)
    p.map(remove_nodata, files)
    # ##-- Create VRT mosaics from single date classifications (without no data
    p = Pool(4)
    p.map(mosaic2vrt_nd0, prefixes)

