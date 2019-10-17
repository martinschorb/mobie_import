#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 24 16:26:45 2019

@author: schorb
"""

import numpy as np
import pyEM as em
import os

import pybdv
from pybdv import transformations as tf

navfile = 'test.nav'

downscale_factors = ([2,2,1],[2,2,1],[4,4,1])


#======================================
            
def write_h5(outname,data1,pxs,mat2,downscale_factors):
    
    outfile = os.path.join('bdv',outname)
    
    if not os.path.exists(outfile+'.h5'):
        print('Converting map '+outname+' into HDF5.')
        pybdv.make_bdv(data1,outfile,downscale_factors=downscale_factors)
        
    tf.write_resolution_and_matrix(outfile+'.xml',outfile+'.xml',[pxs,pxs,10000],mat2)
    

#=======================================




navlines = em.loadtext(navfile)
allitems = em.fullnav(navlines)

if not os.path.exists('bdv'):
    os.makedirs('bdv')

for item in allitems:
    if item['Type'][0] == '2': ## item is a map
        itemname=item['# Item']
        
        print('Processing map '+itemname+' to be added to BDV.')                      
                      
        mergemap = em.mergemap(item)
        
        data = mergemap['im'].copy()
        
        mat = np.linalg.inv(mergemap['matrix'])
        
        mat1=np.concatenate((mat,[[0,float(item['PtsX'][0])],[0,float(item['PtsY'][0])]]),axis=1)
        mat2=np.concatenate((mat1,[[0,0,10000,0],[0,0,0,1]]))
        
        pxs=mergemap['mapheader']['pixelsize'] 
        
        outname = itemname
        
        if (mergemap['mapheader']['stacksize'] == 1 and len(data.shape) > 2):
            for channel in range(data.shape[2]):            
                outname = itemname+'_ch'+str(channel)
                data1 = np.squeeze(data[:,:,channel])
                if data1.max() > 0: write_h5(outname,data1,pxs,mat2,downscale_factors)            
            
        else:            
            write_h5(outname,data,pxs,mat2,downscale_factors)
            
            
                
