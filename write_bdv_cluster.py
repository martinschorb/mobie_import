#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import bdv_tools as bdv

print('this is the script that runs')

c=dict()

c['abc']='def'
c['4'] = 5

print(c)

xfile = '/g/emcf/schorb/code/test.xml'

bdv.dict2xml(c,xfile)

d = bdv.xml2dict(xfile)
