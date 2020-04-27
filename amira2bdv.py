#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import numpy as np
import pyEM as em

import pybdv
from pybdv import transformations as tf
import mrcfile as mrc
import glob
import re
import sys
import os
import xml.etree.ElementTree as ET
from skimage import io

bdv_unit = 'um'

timept = 0

colors=dict()

colors['_R'] = '255 0 0 255'
colors['_G'] = '0 255 0 255'
colors['_B'] = '0 0 255 255'
colors['_W'] = '255 255 255 255'
colors['BF'] = '255 255 255 255'

outformat='.h5'


downscale_factors = list(([1,2,2],[1,2,2],[1,2,2],[1,4,4]))
blow_2d = 1

# from the configuration in our Tecnai, will be used if no specific info can be found
ta_angle = -11.3 

#%%
#=======================================


for file in os.listdir():
    # work on all tform files exported from Amira
    if not file[-5:] == 'tform':
        continue
    else:
        
        #get original file
        
        imfile = file[:-6]
        
        # import transform
        tfile = em.loadtext(file)    
        tform = np.array(list(map(float,tfile[0].split(','))))    
        tform = np.reshape(tform,[4,4])
        
#        print(tform)
        
        #import BoundingBox
        bbox = np.array(list(map(float,tfile[1].split(','))))    
        
        #import voxel size
        voxs = np.array(list(map(float,tfile[2].split(','))))    
        
        # import translation
        trans_0 = np.array(list(map(float,tfile[3].split(','))))  
        
        # import lattice info (double check properties)
        latt = np.array(list(map(float,tfile[4].split(',')[0].split(' x '))))
        
        
        # compensate initial translation (when opening Amira)
        
        trans = trans_0 + [bbox[0],bbox[2],bbox[4]]
        
        setup_id = 0
            
        view=dict()
                            
        view['resolution'] = [pxs,pxs,pxs]
        view['setup_id'] = setup_id
        view['setup_name'] = itemname
        
        view['attributes'] = dict()                       
        
        view['trafo'] = dict()
        
        
exit()


# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx


        mapinfo.append([idx,pxs,itemname,mat])
        
        if os.path.exists(outfile+'.h5'):
            data=np.array([])
        else:
            i=0
            while i<10:                
                if os.path.exists(outfile+'_ch'+str(i)+'.h5'):
                    data=np.array([])
                    outname = itemname+'_ch'+str(i)
                i=i+1
       
        if (mergemap['mapheader']['stacksize'] < 2 and len(data.shape) > 2):
            for channel in range(data.shape[2]):            
                outname = itemname+'_ch'+str(channel)
                data1 = np.squeeze(data[:,:,channel])
                
                if data1.max() > 0: write_h5(outname,data1,pxs,mat2,downscale_factors,blow_2d)            
            
        else:            
            write_h5(outname,data,pxs,mat2,downscale_factors,blow_2d)
        
        
        
        
                
                xval = float(navitem['StageXYZ'][0])
                yval = float(navitem['StageXYZ'][1])
                pos = np.array([xval,yval])
            
        # compensate rotation
        
        phi = np.radians(-ta_angle)
        c = np.cos(phi)
        s = np.sin(phi)
        rotmat = np.array([[c,s],[-s,c]])
        
        #??????
        mat = np.dot(mat,rotmat.T)
        
        # check if volume is from second axis -> additional 90deg rotation
        
        if base[-1]=='b':
            mat = np.dot(mat,np.array([[0,1],[-1,0]]))
            
        
        # determine location of tomogram corners
        xs=mfile.header.nx
        ys=mfile.header.ny
        zs=mfile.header.nz
        
        
        # check if volume is rotated 
        if xs/ys>5:
            zs=ys
            ys=mfile.header.nz
        
        
        
        posx = [-1,-1,1,1]*xs/2
        posy = [-1,1,-1,1]*ys/2
        
        pxcorners = np.array([posy,posx])
        
        corners = np.array(np.dot(mat,pxcorners))+[[pos[0]],[pos[1]]]
        
        
        transl = corners[:,0]#smallestcorner(corners)
        
        
        mat1=np.concatenate((mat,[[0,transl[0]],[0,transl[1]]]),axis=1)        
        mat2=np.concatenate((mat1,np.dot([[0,0,tomopx,-zs/2*tomopx],[0,0,0,1/zstretch]],zstretch)),axis=0)
        
        
        if not os.path.exists(outfile+'.h5'):
            data = mfile.data
            
            
            # check if volume is rotated 
            if data.shape[0]/data.shape[1]>5:
                data = np.swapaxes(data,0,1)
    
            data0 = np.swapaxes(data,0,2)
            data1 = np.fliplr(data0)
            data2 = np.swapaxes(data1,0,2)
        else:
            data2 = []
      
        mfile.close()
        
        write_h5(outname,data2.copy(),[tomopx,tomopx,tomopx*zstretch],mat2,downscale_factors,blow_2d)
            
                
                
                
            
    
                
