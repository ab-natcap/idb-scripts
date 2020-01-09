""" srtm_download.py

Author: Allison Bailey
Date: 2020-01-08

Download SRTM 30m elevation tiles from URL based on a list of tile names
Data URL: http://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/2000.02.11

Filenames look like this:  N25W079.SRTMGL1.hgt.zip

Some tools and tips from NASA
https://lpdaac.usgs.gov/resources/e-learning/how-access-lp-daac-data-command-line/
https://git.earthdata.nasa.gov/projects/LPDUR/repos/daac_data_download_python/browse

use ~/.netrc for user/password

"""
import os
import wget
import requests
from netrc import netrc

### Get list of tiles of interest
data_dir = '/Users/arbailey/natcap/idb/data/source/srtm/nasa'
tile_file= 'idb_tiles30m.csv'
os.chdir(data_dir)
tiles = [line.rstrip('\n') for line in open(tile_file)]

### Create standard SRTM filename based on tile names
srtm_files = ['{}.SRTMGL1.hgt.zip'.format(tile) for tile in tiles]
# srtm_files = ['N15W086.SRTMGL1.hgt.zip']  # sample for testing
print(srtm_files)

# Set up authentication using .netrc file
urs = 'urs.earthdata.nasa.gov'    # Address to call for authentication
netrcDir = os.path.expanduser("~/.netrc")
user = netrc(netrcDir).authenticators(urs)[0]
passwd = netrc(netrcDir).authenticators(urs)[2]

### Download files from USGS website
srtm_url = 'https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/2000.02.11/'
for file in srtm_files:
    file_url = "{}{}".format(srtm_url, file)
    # wget.download(file_url, file)  # using requests instead (below)

    print('Beginning file download with requests {}'.format(file_url))
    # Create and submit request and download file
    with requests.get(file_url, stream=True, auth=(user, passwd)) as response:
        if response.status_code != 200:
            print("{} not downloaded. Verify that your username and password are correct in {}".format(file, netrcDir))
        else:
            response.raw.decode_content = True
            content = response.raw
            with open(file, 'wb') as d:
                while True:
                    chunk = content.read(16 * 1024)
                    if not chunk:
                        break
                    d.write(chunk)
            print('Downloaded file: {}'.format(file))