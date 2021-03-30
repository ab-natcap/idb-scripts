""" mosaic_planet.py

Author: Allison Bailey
Date: 2021-03-23

Mosaic PlanetScope Imagery by date.
"""

import os

base_dir = r'/Users/arbailey/Google Drive/My Drive/planetscope'
base_subdir = 'files/PSScene4Band'

# List all the top level directories with PlanetScope Imagery
psdirlist = [dir for dir in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir,dir))]
print(psdirlist)
# top_dirs = [os.path.join(base_dir, dir) for dir in psdirlist]  # All directories
top_dirs = [os.path.join(base_dir, dir) for dir in psdirlist if "201905" in dir] # subset by criteria

print(top_dirs)

for dir in top_dirs:
    next_dir = os.path.join(dir, base_subdir)
    image_dirs = [dir for dir in os.listdir(next_dir)]
    # print(image_dirs)
    print(next_dir)
    image_files = [os.path.join(next_dir,img_id,'analytic_sr',img_id + '_3B_AnalyticMS_SR.tif') for img_id in image_dirs]
    # print(image_files)
    os.chdir(dir)
    outvrt = 'ps' + image_dirs[0].split('_')[0] + 'analytic_sr.vrt'
    # Need quotes because there is are spaces in the directory name
    infiles = "'" + "'"' '"'".join(image_files) + "'"
    print(outvrt)
    print(infiles)
    os.system('gdalbuildvrt -overwrite ' + outvrt + " " + infiles)


