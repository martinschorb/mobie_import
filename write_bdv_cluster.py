#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import bdv_tools as bdv
import sys
import os

import json


mrcext = ['.join','.mrc','.rec','.st']
tifext = ['.tif','.tiff']


infile = sys.argv[1]
outfile = sys.argv[2]
view_xml = sys.argv[3]
df_str = sys.argv[4]
chunks_str = sys.argv[5]

downscale_factors = list(([1,2,2],[1,2,2],[1,2,2],[1,2,2],[1,4,4]))

chunks = list(map(int,chunks_str.strip('"[]').strip("'").split(',')))

# print(chunks)
# print(downscale_factors)


if len(downscale_factors)<3:downscale_factors = None


print('starting conversion to bdv on the cluster for '+ os.path.basename(infile))

view = json.load(open(view_xml)) #bdv.xml2dict(view_xml)


# read data

if os.path.splitext(infile)[-1].lower() in mrcext:

    import mrcfile as mrc
    import numpy as np

    mfile = mrc.mmap(infile,permissive = 'True')
    data0 = mfile.data


    # check if volume is rotated
    if data0.shape[0]/data0.shape[1]>5:
        data0 = np.swapaxes(data0,0,1)
    
    if mfile.header.mode == 0:
      data0 = np.uint8(data0+127)

    
    data0 = np.swapaxes(data0,0,2)
    data1 = np.fliplr(data0)
    data = np.swapaxes(data1,0,2)

elif os.path.splitext(infile)[-1].lower() in tifext:

    from skimage import io

    data  = io.imread(infile)



bdv.write_bdv(outfile,data,view,blow_2d=1,downscale_factors=downscale_factors,cluster=False,infile=infile,chunks=chunks)

os.remove(view_xml)

print('conversion to bdv on the cluster for '+ os.path.basename(infile) + ' successful.' )
