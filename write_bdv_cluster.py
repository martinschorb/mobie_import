#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import bdv_tools as bdv
import sys


infile = sys.argv[1]
outfile = sys.argv[2]
xml_view = sys.argv[3]
downscale_factors_str = sys.argv[4]

df1 = downscale_factors_str.split('], [')

downscale_factors = list()

for li in df1: downscale_factors.append(list(map(int,li.strip('[]').split(','))))

print('starting conversion to bdv on the cluster for '+infile)

view = bdv.xml2dict(xml_view)

