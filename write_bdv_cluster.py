#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import bdv_tools as bdv
import sys

print('starting conversion to bdv on the cluster')

infile = sys.argv[1]
outfile = sys argv[2]
xml_view = sys.argv[3]

d = bdv.xml2dict(xml_view)


print(infile)
print(outfile)

print(d)
