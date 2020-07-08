#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import bdv_tools as bdv
import sys

print('this is the script that runs')

xfile = sys.argv[1]

d = bdv.xml2dict(xfile)

print(d)
