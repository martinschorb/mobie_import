#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import bdv_tools as bdv
import sys


infile = sys.argv[1]
outfile = sys.argv[2]
view_xml = sys.argv[3]
df_str = sys.argv[4]

downscale_factors = bdv.str2list(df_str)

if len(downscale_factors)<3:downscale_factors = None


print('starting conversion to bdv on the cluster for '+infile)

view = bdv.xml2dict(view_xml)


