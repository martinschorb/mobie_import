# -*- coding: utf-8 -*-
"""
memdistance.py

calculates the distance between two obvious peaks in a variance map across a long image strip
"""

import numpy as np
import skimage as ski
import os
import glob



for file in glob.glob("*.tif"):
    imfile = file
    
    pxs = 0.327
    
    avwsz = 50
    
    avpx = round(avwsz / pxs)
    
    
    
    im1 = ski.io.imread(imfile)
    
    # ignore empty region on the right of the image
    start = 80
    
    roilength = im1.shape[0]
    
    mem_distance = np.array([])
    
    windows = np.linspace(0,roilength-avpx,int(np.floor((roilength-avpx)/avpx))+1).astype(int)
    
    for windowstart in windows:
        region = im1[windowstart:windowstart+avpx,start:]
        profile = np.mean(region,0)
        grad = np.gradient(profile)    
        
        # first major slope
        minidx1 = np.argmin(grad)
        
        # find zero crossing before&after this:
        peak1 = minidx1-(np.where(np.diff(np.sign(np.flip(grad[:minidx1])))>0))[0][0]-1
        
        nextzeros = np.where(np.diff(np.sign(grad[minidx1:]))>0)
        
        if not np.size(nextzeros)==0:
            base1 = nextzeros[0][0] + minidx1 + 1
            minidx2 = np.argmin(grad[base1:])+base1
            
            # next peak to the right?
            if np.min(grad[base1:])<0:
                peak2 = minidx2-(np.where(np.diff(np.sign(np.flip(grad[base1:minidx2])))>0))[0][0]-1
                distance = (peak2-peak1) * pxs
            
            else:
            # other peak is on the left
                    minidx2 = np.argmin(grad[:peak1])
                    peak2 = minidx2-(np.where(np.diff(np.sign(np.flip(grad[:minidx1])))>0))[0][0]-1
            
                    base1 = (np.where(np.diff(np.sign(grad[minidx1:]))>0))[0][0]+minidx1+1
            
                    distance = (peak1 - peak2) * pxs
        else:
        # other peak is on the left
            minidx2 = np.argmin(grad[:peak1])
            peak2 = minidx2-(np.where(np.diff(np.sign(np.flip(grad[:minidx1])))>0))[0][0]-1
    
            distance = (peak1 - peak2) * pxs
     
        mem_distance = np.append(mem_distance,distance)
        
    np.savetxt(imfile+'_analysis.csv',np.array([windows,windows*pxs,mem_distance]).T,fmt='%0.2f',delimiter=',')
