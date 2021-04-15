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

input_dir = r'/Users/arbailey/Google Drive/My Drive/sargassum/s2toa_classified'

gdal_nodata_command = 'gdal_edit.py -a_nodata -9999 {classed_tile}'

# https://courses.spatialthoughts.com/gdal-tools.html#running-commands-in-batch
def add_nodata(file):
    input = os.path.join(input_dir, file)
    # filename = os.path.splitext(os.path.basename(file))[0]
    # output = os.path.join(input_dir, filename + '.tif')
    # os.system(gdal_nodata_command.format(classed_tile=input)) # doesn't work with space in filename
    os.system('gdal_edit.py -a_nodata -9999 ' + '"' + input + '"')

def mosaic2vrt(prefix):
    start_dir = os.getcwd()
    os.chdir(input_dir)
    outfile = prefix + '_mosaic.vrt'
    infiles = prefix + '*.tif'
    print(outfile)
    os.system('gdalbuildvrt -overwrite ' + outfile + " " + infiles)
    os.chdir(start_dir)
    # gdalbuildvrt -overwrite wam_srtm_hba_BhmMAR.vrt wam_hba*.tif




if __name__ == '__main__':

    files = [file for file in os.listdir(input_dir) if file.endswith('.tif')]

    prefixes = []
    for f in files:
        prefix = f.split('_')[0]
        if not prefix in prefixes:
            prefixes.append(prefix)
    print(prefixes)

    ##--- Add No Data value to TIF files
    # Multiprocess addition of No Data Value - 5 seconds
    # start = timer()
    p = Pool(4)
    p.map(add_nodata, files)
    # end = timer()
    # print(end - start)
    # Single Process - 20 seconds
    # start = timer()
    # for file in files:
    #     add_nodata(file)
    # end = timer()
    # print(end - start)

    ##-- Create VRT mosaics from single date classifications
    p = Pool(4)
    p.map(mosaic2vrt, prefixes)

