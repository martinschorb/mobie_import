#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import bdv_tools as bdv

print('this is the script that runs')

c=dict()

c['abc']='def'
c['4'] = 5

bdv.dict2xml(c,'/g/emcf/cshorb/code/test.xml')
