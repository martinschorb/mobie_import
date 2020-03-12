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


downscale_factors = ([1,2,2],[1,2,2],[1,2,2],[1,4,4])


#%%

#======================================
            
def write_h5(outname,data,pxs,mat2,downscale_factors,blow_2d):
    
    outfile = os.path.join('bdv',outname)
    
        
    
    if not os.path.exists(outfile+'.h5'):
        ndim = data.ndim
        if ndim > 2: assert ndim == 3, "Only support 3d"
            #assert len(resolution) == ndim
        if ndim < 3: 
            assert ndim == 2, "Only support 2d"
            data=np.expand_dims(data.copy(),axis=0)
#            data1=np.concatenate((d1,d1),axis=0)
        
        if data.dtype.kind=='i':
            if data.dtype.itemsize == 1:
                data0 = np.uint8(data-data.min())
            elif data.dtype.itemsize == 2:
                data0 = np.uint16(data-data.min())
            else:
                data0 = np.uint16((data-data.min())/data.max()*65535)
        else:
            data0 = data.copy()
        
        
        
        print('Converting map '+outname+' into HDF5.')
        data0[data0==0]=1
        
        pybdv.make_bdv(data0,outfile,downscale_factors=downscale_factors,setup_name=outname)
    
    if type(pxs)==float or type(pxs)==np.float64:
        scale = [pxs,pxs,blow_2d]
        mat2[2,2] = blow_2d
        mat2[2,3] = 0#-blow_2d/2
    elif len(pxs) == 1:
        scale = [pxs,pxs,blow_2d]
        mat2[2,2] = blow_2d
        mat2[2,3] = 0#-blow_2d/2
    elif len(pxs) == 3:
        scale = pxs
    else:
        print('Pixelsize was wrongly defined!!!')
        
        
        
    tf.write_resolution_and_matrix(outfile+'.xml',outfile+'.xml',scale,mat2)
    

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
            
                
                
                
            
    
                
